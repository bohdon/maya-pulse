
import logging
from functools import partial
import maya.cmds as cmds
import maya.OpenMaya as api
import pymel.core as pm
import pymetanode as meta

import pulse.core

__all__ = [
    'BlueprintChangeEvents',
    'BlueprintEventsMixin',
    'BlueprintLifecycleEvents',
    'Event',
    'MayaCallbackEvents',
]

LOG = logging.getLogger(__name__)


class Event(list):
    """
    A list of callable objects. Calling an Event
    will cause a call to each item in the list in order.
    """
    def __call__(self, *args, **kwargs):
        for func in self:
            func(*args, **kwargs)

    def __repr__(self):
        return "Event(%s)" % list.__repr__(self)

    def appendUnique(self, item):
        if item not in self:
            self.append(item)

    def removeAll(self, item):
        while item in self:
            self.remove(item)


class MayaCallbackEvents(object):
    """
    Base for any event dispatcher that will make use
    of Maya api MMessage callbacks.

    Provides functionality for easy callback management
    to make sure callbacks are not redundantly registered
    and are properly removed.
    """

    def __init__(self):
        # have maya callbacks been registered?
        self._areMayaCallbacksRegistered = False
        # list of maya callback IDs that have been registered
        self._callbackIDs = []
        # list of objects that are subscribed to any events
        # used to determine if maya callbacks should be registered
        self._subscribers = []

    def __del__(self):
        self._unregisterMayaCallbacks()

    def _registerMayaCallbacks(self):
        """
        Register all Maya callbacks for this dispatcher.
        Does nothing if callbacks are already registered.
        """
        if not self._areMayaCallbacksRegistered:
            self._areMayaCallbacksRegistered = True
            self._callbackIDs = list(self._addMayaCallbacks())
            LOG.debug('{0}._registerMayaCallbacks'.format(self.__class__.__name__))

    def _addMayaCallbacks(self):
        """
        Should be overridden in subclasses to register any Maya callbacks.
        Must return a list of callback IDs for all newly added callbacks.
        This will only be called if callbacks are not already registered.
        """
        return []

    def _unregisterMayaCallbacks(self):
        """
        Unregister all Maya callbacks, if currently registered.
        """
        if self._areMayaCallbacksRegistered:
            self._areMayaCallbacksRegistered = False
            for cbId in self._callbackIDs:
                api.MMessage.removeCallback(cbId)
            self._callbackIDs = []
            LOG.debug('{0}._unregisterMayaCallbacks'.format(self.__class__.__name__))

    def addSubscriber(self, subscriber):
        """
        Add a subscriber to this event dispatcher
        """
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
        if self._subscribers:
            self._registerMayaCallbacks()

    def removeSubscriber(self, subscriber):
        """
        Remove a subscriber from this event dispatcher
        """
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
        if not self._subscribers:
            self._unregisterMayaCallbacks()




class BlueprintLifecycleEvents(MayaCallbackEvents):
    """
    A singular object responsible for dispatching
    Blueprint creation and deletion events.

    Events:
        onBlueprintCreated(node):
            Called when any Blueprint is created. Passes
            the newly created Blueprint node.
        onBlueprintDeleted(node):
            Called when any Blueprint is deleted. Passes
            the Blueprint node that is being deleted.
    """

    # the shared events instance
    INSTANCE = None

    @classmethod
    def getShared(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = cls()
        return cls.INSTANCE

    def __init__(self):
        super(BlueprintLifecycleEvents, self).__init__()
        self.onBlueprintCreated = Event()
        self.onBlueprintDeleted = Event()

    # override
    def _addMayaCallbacks(self):
        # blueprint nodes are always of type 'network'
        addId = api.MDGMessage.addNodeAddedCallback(self._onNodeAdded, 'network')
        removeId = api.MDGMessage.addNodeRemovedCallback(self._onNodeRemoved, 'network')
        return (addId, removeId)

    def _onNodeAdded(self, node, *args):
        """
        Args:
            node: A MObject node that was just added
        """
        # no way to know if it's a Blueprint yet,
        # defer until later and check the node again
        # TODO: do this more precisely, don't use deferred

        mfn = api.MFnDependencyNode(node)
        if mfn.typeName() != 'network':
            # blueprints are network nodes
            return
        
        cmds.evalDeferred(
            partial(self._onNodeAddedDeferred, mfn.name()), evaluateNext=True)

    def _onNodeAddedDeferred(self, fullName):
        """
        Args:
            fullName: A string full name of a node that was added
        """
        node = meta.getMObject(fullName)
        if node:
            if pulse.core.Blueprint.isBlueprintNode(node):
                LOG.debug("onBlueprintCreated('{0}')".format(node))
                self.onBlueprintCreated(pm.PyNode(node))
        else:
            LOG.debug(
                "Failed to locate node: {0}".format(fullName))

    def _onNodeRemoved(self, node, *args):
        """
        Args:
            node: A MObject node that is being removed
        """
        # TODO: this is a hack to identify a blueprint node being deleted
        #       that no longer counts as a valid blueprint because its data
        #       has been removed. needs improvement
        if (api.MFnDependencyNode(node).name() == pulse.core.BLUEPRINT_NODENAME or
                pulse.core.Blueprint.isBlueprintNode(node)):
            LOG.debug("onBlueprintDeleted('{0}')".format(node))
            self.onBlueprintDeleted(pm.PyNode(node))


class BlueprintChangeEvents(MayaCallbackEvents):
    """
    An event dispatcher specific to a Blueprint node in the
    scene. Fires events whenever the Blueprint node is modified.

    Events:
        onBlueprintNodeChanged(node):
            Called when the blueprint changes, passes the Blueprint
            node that was modified.
    """

    # shared event instances, mapped by blueprint node names
    INSTANCES = {}

    @classmethod
    def getShared(cls, blueprintNodeName):
        """
        Return a shared BlueprintChangeEvents instance for a specific
        Blueprint node, creating a new instance if necessary.

        Returns None if the node does not exist.
        """
        # perform instance cleanup
        cls.cleanupSharedInstances()
        if not cmds.objExists(blueprintNodeName):
            return
        if blueprintNodeName not in cls.INSTANCES:
            cls.INSTANCES[blueprintNodeName] = cls(blueprintNodeName)
        else:
            cls.INSTANCES[blueprintNodeName].refreshMayaCallbacks()
        return cls.INSTANCES[blueprintNodeName]

    @classmethod
    def cleanupSharedInstances(cls):
        for nodeName, inst in cls.INSTANCES.items():
            if not inst.nodeExists():
                del cls.INSTANCES[nodeName]

    def __init__(self, blueprintNodeName):
        super(BlueprintChangeEvents, self).__init__()
        self.blueprintNodeName = blueprintNodeName
        self.lastUUID = None
        self.onBlueprintNodeChanged = Event()

    def nodeExists(self):
        """
        Return True if the Blueprint node exists
        """
        return cmds.objExists(self.blueprintNodeName)

    def refreshMayaCallbacks(self):
        """
        Check if the node that was originally used in the callback has changed,
        and if so, recreate the callback using the new node.
        """
        if self._areMayaCallbacksRegistered:
            uuid = meta.getUUID(self.blueprintNodeName)
            if self.lastUUID != uuid:
                LOG.debug('uuid changed, refreshing callbacks')
                self._unregisterMayaCallbacks()
                self._registerMayaCallbacks()

    # override
    def _addMayaCallbacks(self):
        mobject = meta.getMObject(self.blueprintNodeName)
        if not mobject:
            return []
        changeId = api.MNodeMessage.addAttributeChangedCallback(mobject, self._onBlueprintAttrChanged)
        # record node uuid at the time of adding the callback
        self.lastUUID = meta.getUUID(self.blueprintNodeName)
        return (changeId,)

    def _onBlueprintAttrChanged(self, changeType, srcPlug, dstPlug, clientData):
        if srcPlug.partialName() == 'pyMetaData':
            self.onBlueprintNodeChanged(pm.PyNode(srcPlug.node()))



class BlueprintEventsMixin(object):
    """
    A mixin for listening to shared events related
    to Blueprint changes, including the creation or
    deletion of a Blueprint.
    """

    def enableBlueprintEvents(self):
        """
        Enable Blueprint lifecycle events on this object.
        """
        lifeEvents = BlueprintLifecycleEvents.getShared()
        lifeEvents.onBlueprintCreated.appendUnique(self._onBlueprintCreatedInternal)
        lifeEvents.onBlueprintDeleted.appendUnique(self.onBlueprintDeleted)
        lifeEvents.addSubscriber(self)

    def disableBlueprintEvents(self):
        """
        Disable Blueprint events on this object
        """
        lifeEvents = BlueprintLifecycleEvents.getShared()
        lifeEvents.onBlueprintCreated.removeAll(self._onBlueprintCreatedInternal)
        lifeEvents.onBlueprintDeleted.removeAll(self.onBlueprintDeleted)
        lifeEvents.removeSubscriber(self)

    def enableBlueprintChangeEvents(self, blueprintNodeName):
        """
        Enable events for any changes made to a Blueprint node.

        Args:
            blueprintNodeName: A string name of a valid Blueprint node
        """
        if self._getSubscribedBlueprintName() != blueprintNodeName:
            self.disableBlueprintChangeEvents()
            self.subscribeToBlueprint = blueprintNodeName
            self._subscribeToBlueprintChanges()

    def disableBlueprintChangeEvents(self):
        """
        Disable events for any changes made to the currently subscribed Blueprint node.
        Note that this does not need to be called for Blueprints that are deleted.
        Does nothing if not subscribed to a Blueprint.

        Args:
            blueprintNodeName: A string name of a valid Blueprint node
        """
        if self._getSubscribedBlueprintName() is not None:
            self._unsubscribeToBlueprintChanges()
            self.subscribeToBlueprint = None

    def _subscribeToBlueprintChanges(self):
        """
        Attempt to subscribe to any changes for the current blueprint.
        Does nothing if the blueprint doesn't exist or no blueprint node
        name has been set for subscription.
        """
        if self._getSubscribedBlueprintName() is not None:
            changeEvents = BlueprintChangeEvents.getShared(self.subscribeToBlueprint)
            if changeEvents:
                changeEvents.onBlueprintNodeChanged.appendUnique(self.onBlueprintNodeChanged)
                changeEvents.addSubscriber(self)
                LOG.debug("Subscribed to blueprint change events for: " + self.subscribeToBlueprint)


    def _unsubscribeToBlueprintChanges(self):
        if self._getSubscribedBlueprintName() is not None:
            changeEvents = BlueprintChangeEvents.getShared(self.subscribeToBlueprint)
            if changeEvents:
                changeEvents.onBlueprintNodeChanged.removeAll(self.onBlueprintNodeChanged)
                changeEvents.removeSubscriber(self)
                LOG.debug("Unsubscribed from blueprint change events for: " + self.subscribeToBlueprint)

    def _getSubscribedBlueprintName(self):
        if not hasattr(self, 'subscribeToBlueprint'):
            self.subscribeToBlueprint = None
        return self.subscribeToBlueprint

    def _onBlueprintCreatedInternal(self, node):
        if self._getSubscribedBlueprintName() == node.nodeName():
            self._subscribeToBlueprintChanges()
        self.onBlueprintCreated(node)

    def onBlueprintCreated(self, node):
        pass

    def onBlueprintNodeChanged(self, node):
        pass

    def onBlueprintDeleted(self, node):
        pass



class RigLifecycleEvents(MayaCallbackEvents):
    """
    A singular object responsible for dispatching
    Rig creation and deletion events.

    Events:
        onRigCreated(node):
            Called when any rig is created. Passes
            the newly created rig node.
        onRigDeleted(node):
            Called when any rig is deleted. Passes
            the rig node that is being deleted.
    """

    # the shared events instance
    INSTANCE = None

    @classmethod
    def getShared(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = cls()
        return cls.INSTANCE

    def __init__(self):
        super(RigLifecycleEvents, self).__init__()
        self.onRigCreated = Event()
        self.onRigDeleted = Event()

    # override
    def _addMayaCallbacks(self):
        # rig nodes are always of type 'transform'
        addId = api.MDGMessage.addNodeAddedCallback(self._onNodeAdded, 'transform')
        removeId = api.MDGMessage.addNodeRemovedCallback(self._onNodeRemoved, 'transform')
        return (addId, removeId)

    def _onNodeAdded(self, node, *args):
        """
        Args:
            node: A MObject node that was just added
        """
        # no way to know if it's a Rig yet,
        # defer until later and check the node again
        # TODO: do this more precisely, don't use deferred

        mfn = api.MFnDependencyNode(node)
        if mfn.typeName() != 'transform':
            # rig nodes must be transforms
            return
        
        fullName = api.MFnDagNode(node).fullPathName()
        cmds.evalDeferred(
            partial(self._onNodeAddedDeferred, fullName), evaluateNext=True)

    def _onNodeAddedDeferred(self, fullName, *args):
        """
        Args:
            fullName: A string full name of a node that was added
        """
        node = meta.getMObject(fullName)
        if node:
            if pulse.core.isRig(node):
                LOG.debug("onRigCreated('{0}')".format(node))
                self.onRigCreated(pm.PyNode(node))
        else:
            LOG.debug(
                "Failed to locate node: {0}".format(fullName))

    def _onNodeRemoved(self, node, *args):
        """
        Args:
            node: A MObject node that is being removed
        """
        if pulse.core.isRig(node):
            LOG.debug("onRigDeleted('{0}')".format(node))
            self.onRigDeleted(pm.PyNode(node))


class RigEventsMixin(object):
    """
    A mixin for listening to shared events related
    to Rig events, such as creation and deletion
    """

    def enableRigEvents(self):
        """
        Enable Rig lifecycle events on this object.
        """
        lifeEvents = RigLifecycleEvents.getShared()
        lifeEvents.onRigCreated.appendUnique(self.onRigCreated)
        lifeEvents.onRigDeleted.appendUnique(self.onRigDeleted)
        lifeEvents.addSubscriber(self)

    def disableRigEvents(self):
        """
        Disable Rig events on this object
        """
        lifeEvents = RigLifecycleEvents.getShared()
        lifeEvents.onRigCreated.removeAll(self.onRigCreated)
        lifeEvents.onRigDeleted.removeAll(self.onRigDeleted)
        lifeEvents.removeSubscriber(self)

    def onRigCreated(self, node):
        pass

    def onRigDeleted(self, node):
        pass

