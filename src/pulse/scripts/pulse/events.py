import logging
from functools import partial

import maya.OpenMaya as api
import maya.cmds as cmds
import pymel.core as pm

from .vendor import pymetanode as meta
from .rigs import is_rig

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

    def append_unique(self, item):
        if item not in self:
            self.append(item)

    def remove_all(self, item):
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
        self._unregister_maya_callbacks()

    def _register_maya_callbacks(self):
        """
        Register all Maya callbacks for this dispatcher.
        Does nothing if callbacks are already registered.
        """
        if not self._areMayaCallbacksRegistered:
            self._areMayaCallbacksRegistered = True
            self._callbackIDs = list(self._add_maya_callbacks())
            LOG.debug("%s._register_maya_callbacks", self.__class__.__name__)

    def _add_maya_callbacks(self):
        """
        Should be overridden in subclasses to register any Maya message callbacks.
        This will only be called if callbacks are not already registered.

        Returns:
            A list of callback IDs for all newly added callbacks.
        """
        return []

    def _unregister_maya_callbacks(self):
        """
        Unregister all Maya callbacks, if currently registered.
        """
        if self._areMayaCallbacksRegistered:
            self._areMayaCallbacksRegistered = False
            for cbId in self._callbackIDs:
                api.MMessage.removeCallback(cbId)
            self._callbackIDs = []
            LOG.debug("%s._unregister_maya_callbacks", self.__class__.__name__)

    def add_subscriber(self, subscriber):
        """
        Add a subscriber to this event dispatcher
        """
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
        if self._subscribers:
            self._register_maya_callbacks()

    def remove_subscriber(self, subscriber):
        """
        Remove a subscriber from this event dispatcher
        """
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
        if not self._subscribers:
            self._unregister_maya_callbacks()


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
    def get_shared(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = cls()
        return cls.INSTANCE

    def __init__(self):
        super(RigLifecycleEvents, self).__init__()
        self.onRigCreated = Event()
        self.onRigDeleted = Event()

    # override
    def _add_maya_callbacks(self):
        # rig nodes are always of type 'transform'
        add_id = api.MDGMessage.addNodeAddedCallback(self._on_node_added, "transform")
        remove_id = api.MDGMessage.addNodeRemovedCallback(self._on_node_removed, "transform")
        return add_id, remove_id

    def _on_node_added(self, node, *args):
        """
        Args:
            node: A MObject node that was just added
        """
        # no way to know if it's a Rig yet, defer until later and check the node again
        # TODO: do this more precisely, don't use deferred

        mfn = api.MFnDependencyNode(node)
        if mfn.typeName() != "transform":
            # rig nodes must be transforms
            return

        full_name = api.MFnDagNode(node).fullPathName()
        cmds.evalDeferred(partial(self._on_node_added_deferred, full_name), evaluateNext=True)

    def _on_node_added_deferred(self, full_name, *args):
        """
        Args:
            full_name: A string full name of a node that was added
        """
        node = meta.getMObject(full_name)
        if node:
            if is_rig(node):
                self.onRigCreated(pm.PyNode(node))

    def _on_node_removed(self, node, *args):
        """
        Args:
            node: A MObject node that is being removed
        """
        if is_rig(node):
            self.onRigDeleted(pm.PyNode(node))
