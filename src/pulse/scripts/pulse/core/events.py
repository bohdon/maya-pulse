
import logging
from functools import partial
import maya.cmds as cmds
import maya.OpenMaya as api
import pymel.core as pm
import pymetanode as meta

from .blueprints import Blueprint
from .rigs import isRig

__all__ = [
    'Event',
    'MayaCallbackEvents',
    'RigEventsMixin',
    'RigLifecycleEvents',
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
            LOG.debug('{0}._registerMayaCallbacks'.format(
                self.__class__.__name__))

    def _addMayaCallbacks(self):
        """
        Should be overridden in subclasses to register any Maya
        message callbacks. This will only be called if callbacks
        are not already registered.

        Returns:
            A list of callback IDs for all newly added callbacks.
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
            LOG.debug('{0}._unregisterMayaCallbacks'.format(
                self.__class__.__name__))

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
        addId = api.MDGMessage.addNodeAddedCallback(
            self._onNodeAdded, 'transform')
        removeId = api.MDGMessage.addNodeRemovedCallback(
            self._onNodeRemoved, 'transform')
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
            if isRig(node):
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
        if isRig(node):
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
