

from functools import partial
import maya.cmds as cmds
import maya.OpenMaya as api
import pymetanode as meta

import pulse.core

__all__ = [
    'BlueprintChangeEvents',
    'BlueprintEventsMixin',
    'BlueprintLifecycleEvents',
    'Event',
    'MayaCallbackEvents',
]


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
    
    def notifySubscriberAdded(self, subscriber):
        """
        Notify this event dispatcher that an object has subscribed
        to one or more events.
        """
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
        if self._subscribers:
            self._registerMayaCallbacks()
    
    def notifySubscriberRemoved(self, subscriber):
        """
        Notify this event dispatcher that an object has
        unsubscribed to all events.
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
        onBlueprintCreated(blueprintNode):
            Called when any Blueprint is created. Passes
            the newly created Blueprint node (MObject).
        onBlueprintDeleted(blueprintNode):
            Called when any Blueprint is deleted. Passes
            the Blueprint node (MObject) that is being deleted.
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
        # no way to know if it's a Blueprint yet,
        # defer until later and check the node again
        cmds.evalDeferred(partial(self._onNodeAddedDeferred, node, *args))

    def _onNodeAddedDeferred(self, node, *args):
        if pulse.core.Blueprint.isBlueprintNode(node):
            self.onBlueprintCreated(node)

    def _onNodeRemoved(self, node, *args):
        if pulse.core.Blueprint.isBlueprintNode(node):
            self.onBlueprintDeleted(node)


class BlueprintChangeEvents(MayaCallbackEvents):
    """
    An event dispatcher specific to a Blueprint node in the
    scene. Fires events whenever the Blueprint node is modified.

    Events:
        onBlueprintChanged(blueprintNode):
            Called when the blueprint changes, passes the Blueprint
            node (MObject) that was modified.
    """

    # shared event instances, mapped by blueprint node names
    INSTANCES = {}

    @classmethod
    def getShared(cls, blueprintNodeName):
        # perform instance cleanup
        cls.cleanupSharedInstances()
        nodeName = blueprintNodeName
        if nodeName not in cls.INSTANCES:
            cls.INSTANCES[nodeName] = cls(blueprintNodeName)
        return cls.INSTANCES[nodeName]

    @classmethod
    def cleanupSharedInstances(cls):
        for nodeName in cls.INSTANCES.keys():
            if not cmds.objExists(nodeName):
                del cls.INSTANCES[nodeName]

    def __init__(self, blueprintNodeName):
        super(BlueprintChangeEvents, self).__init__()
        self.blueprintNodeName = blueprintNodeName
        self.onBlueprintChanged = Event()

    # override
    def _addMayaCallbacks(self):
        mobject = meta.getMObject(self.blueprintNodeName)
        if not mobject:
            return []
        changeId = api.MNodeMessage.addAttributeChangedCallback(mobject, self._onBlueprintAttrChanged)
        return changeId

    def _onBlueprintAttrChanged(self, changeType, srcPlug, dstPlug, clientData):
        if srcPlug.partialName() == 'pyMetaData':
            self.onBlueprintChanged(srcPlug.node())



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
        if self.onBlueprintCreated not in lifeEvents.onBlueprintCreated:
            lifeEvents.onBlueprintCreated.append(self.onBlueprintCreated)
        if self.onBlueprintDeleted not in lifeEvents.onBlueprintDeleted:
            lifeEvents.onBlueprintDeleted.append(self.onBlueprintDeleted)
        lifeEvents.notifySubscriberAdded(self)

    def disableBlueprintEvents(self):
        """
        Disable Blueprint events on this object
        """
        lifeEvents = BlueprintLifecycleEvents.getShared()
        if self.onBlueprintCreated in lifeEvents.onBlueprintCreated:
            lifeEvents.onBlueprintCreated.remove(self.onBlueprintCreated)
        if self.onBlueprintDeleted in lifeEvents.onBlueprintDeleted:
            lifeEvents.onBlueprintDeleted.remove(self.onBlueprintDeleted)
        lifeEvents.notifySubscriberRemoved(self)

    def enableBlueprintChangeEvents(self, blueprintNodeName):
        """
        Enable events for any changes made to a Blueprint node.

        Args:
            blueprintNodeName: A string name of a valid Blueprint node
        """
        changeEvents = BlueprintChangeEvents.getShared(blueprintNodeName)
        if changeEvents:
            if self.onBlueprintChanged not in changeEvents.onBlueprintChanged:
                changeEvents.onBlueprintChanged.append(self.onBlueprintChanged)
            changeEvents.notifySubscriberAdded(self)

    def disableBlueprintChangeEvents(self, blueprintNodeName):
        """
        Disable events for any changes made to a Blueprint node.
        Note that this does not need to be called for Blueprints that are deleted.

        Args:
            blueprintNodeName: A string name of a valid Blueprint node
        """
        changeEvents = BlueprintChangeEvents.getShared(blueprintNodeName)
        if changeEvents:
            if self.onBlueprintChanged in changeEvents.onBlueprintChanged:
                changeEvents.onBlueprintChanged.remove(self.onBlueprintChanged)
            changeEvents.notifySubscriberRemoved(self)

    def onBlueprintCreated(self, blueprintNode):
        pass

    def onBlueprintChanged(self, blueprintNode):
        pass

    def onBlueprintDeleted(self, blueprintNode):
        pass



class RigLifecycleEvents(MayaCallbackEvents):
    """
    A singular object responsible for dispatching
    Rig creation and deletion events.

    Events:
        onRigCreated(rigNode):
            Called when any rig is created. Passes
            the newly created rig node (MObject).
        onRigDeleted(rigNode):
            Called when any rig is deleted. Passes
            the rig node (MObject) that is being deleted.
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
        # no way to know if it's a Rig yet,
        # defer until later and check the node again
        cmds.evalDeferred(partial(self._onNodeAddedDeferred, node, *args))

    def _onNodeAddedDeferred(self, node, *args):
        if pulse.core.isRig(node):
            self.onRigCreated(node)

    def _onNodeRemoved(self, node, *args):
        if pulse.core.isRig(node):
            self.onRigDeleted(node)


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
        if self.onRigCreated not in lifeEvents.onRigCreated:
            lifeEvents.onRigCreated.append(self.onRigCreated)
        if self.onRigDeleted not in lifeEvents.onRigDeleted:
            lifeEvents.onRigDeleted.append(self.onRigDeleted)
        lifeEvents.notifySubscriberAdded(self)

    def disableRigEvents(self):
        """
        Disable Rig events on this object
        """
        lifeEvents = RigLifecycleEvents.getShared()
        if self.onRigCreated in lifeEvents.onRigCreated:
            lifeEvents.onRigCreated.remove(self.onRigCreated)
        if self.onRigDeleted in lifeEvents.onRigDeleted:
            lifeEvents.onRigDeleted.remove(self.onRigDeleted)
        lifeEvents.notifySubscriberRemoved(self)

    def onRigCreated(self, rigNode):
        pass

    def onRigDeleted(self, rigNode):
        pass

