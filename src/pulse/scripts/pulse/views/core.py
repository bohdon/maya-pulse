
from functools import partial
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import maya.OpenMaya as om
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import pulse

__all__ = [
    'buttonCommand',
    'CollapsibleFrame',
    'PulseWindow',
    'UIEventMixin',
]

def buttonCommand(func, *args, **kwargs):
    """
    Return a function that can be called which will execute
    the given function with proper undo chunk handling.
    """

    def wrapper():
        cmds.undoInfo(openChunk=True)
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)
        finally:
            cmds.undoInfo(closeChunk=True)
    
    return wrapper


class CollapsibleFrame(QtWidgets.QFrame):

    collapsedChanged = QtCore.Signal(bool)

    def __init__(self, parent):
        super(CollapsibleFrame, self).__init__(parent)
        self._isCollapsed = False
    
    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setIsCollapsed(not self._isCollapsed)
        else:
            return super(CollapsibleFrame, self).mouseReleaseEvent(QMouseEvent)
    
    def setIsCollapsed(self, newCollapsed):
        self._isCollapsed = newCollapsed
        self.collapsedChanged.emit(self._isCollapsed)
    
    def isCollapsed(self):
        return self._isCollapsed


class UIEventMixin(object):
    """
    A mixin for listening to shared events related
    to pulse scene changes, such as the creation or
    deletion of a Blueprint.
    """

    # the list of currently active ui objects listening for events
    _LISTENERS = []
    # is the mixin globally registered with maya callbacks?
    _IS_REGISTERED = False
    # the MCallbackIDs of registered messages
    _MSGIDS = []
    # a flag for preventing redundant deferred node updates
    _NODES_DIRTY = False
    
    @staticmethod
    def _registerUIEventCallbacks():
        """
        Add MMessage callbacks for necessary Maya events
        """
        if not UIEventMixin._IS_REGISTERED:
            UIEventMixin._IS_REGISTERED = True
            ids = []
            ids.append(om.MDGMessage.addNodeAddedCallback(UIEventMixin._onNodesChanged, 'network'))
            ids.append(om.MDGMessage.addNodeRemovedCallback(UIEventMixin._onNodesChanged, 'network'))
            ids.append(om.MDGMessage.addNodeAddedCallback(UIEventMixin._onNodesChanged, 'transform'))
            ids.append(om.MDGMessage.addNodeRemovedCallback(UIEventMixin._onNodesChanged, 'transform'))
            UIEventMixin._MSGIDS = ids
    
    @staticmethod
    def _unregisterUIEventCallbacks():
        """
        Remove all registered MMessage callbacks
        """
        if UIEventMixin._IS_REGISTERED:
            UIEventMixin._IS_REGISTERED = False
            if UIEventMixin._MSGIDS:
                for id in UIEventMixin._MSGIDS:
                    om.MMessage.removeCallback(id)
                UIEventMixin._MSGIDS = []

    @staticmethod
    def _nodeAdded(node, *args):
        UIEventMixin._onNodesChanged()

    @staticmethod
    def _onNodesChanged(node, *args):
        # queue deferred change event only once per scene changes
        if not UIEventMixin._NODES_DIRTY:
            UIEventMixin._NODES_DIRTY = True
            cmds.evalDeferred(UIEventMixin._onNodesChangedDeferred)
    
    @staticmethod
    def _onNodesChangedDeferred():
        """
        Called when relevant nodes are added or removed.
        Used to check for changes in blueprints or rigs.
        """
        UIEventMixin._NODES_DIRTY = False
        blueprintExists = pulse.Blueprint.doesDefaultNodeExist()
        rigExists = len(pulse.getAllRigs()) > 0
        for listener in UIEventMixin._LISTENERS:
            listener.setBlueprintExists(blueprintExists)
            listener.setRigExists(rigExists)
    
    def enableUIMixinEvents(self):
        """
        Enable events on this object
        """
        if self not in UIEventMixin._LISTENERS:
            UIEventMixin._LISTENERS.append(self)
        UIEventMixin._registerUIEventCallbacks()

        self.blueprintExists = pulse.Blueprint.doesDefaultNodeExist()
        self.rigExists = len(pulse.getAllRigs()) > 0
    
    def disableUIMixinEvents(self):
        """
        Disable events on this object
        """
        if self in UIEventMixin._LISTENERS:
            UIEventMixin._LISTENERS.remove(self)
        if not UIEventMixin._LISTENERS:
            UIEventMixin._unregisterUIEventCallbacks()
    
    def setBlueprintExists(self, newExists):
        if newExists != self.blueprintExists:
            self.blueprintExists = newExists
            if self.blueprintExists:
                self.onBlueprintCreated()
            else:
                self.onBlueprintDeleted()
    
    def setRigExists(self, newExists):
        if newExists != self.rigExists:
            self.rigExists = newExists
            if self.rigExists:
                self.onRigCreated()
            else:
                self.onRigDeleted()
    
    def onBlueprintCreated(self):
        pass
    
    def onBlueprintDeleted(self):
        pass
    
    def onRigCreated(self):
        pass
    
    def onRigDeleted(self):
        pass


class PulseWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):

    OBJECT_NAME = None

    @classmethod
    def createAndShow(cls):
        cls.deleteInstances()
        window = cls()
        window.show()
        return window
    
    @classmethod
    def exists(cls):
        """
        Return True if an instance of this window exists
        """
        result = False
        if cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True):
            result = True
        if cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True):
            result = True
        if cmds.window(cls.OBJECT_NAME, q=True, ex=True):
            result = True
        return result

    @classmethod
    def deleteInstances(cls):
        """
        Delete existing instances of this window
        """
        result = False
        # close and delete an existing workspace control
        if cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True):
            cmds.workspaceControl(cls.getWorkspaceControlName(), e=True, close=True)
            result = True
        if cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True):
            cmds.deleteUI(cls.getWorkspaceControlName(), control=True)
            result = True
        if cmds.window(cls.OBJECT_NAME, q=True, ex=True):
            cmds.deleteUI(cls.OBJECT_NAME, window=True)
            result = True
        return result

    @classmethod
    def getWorkspaceControlName(cls):
        return cls.OBJECT_NAME + 'WorkspaceControl'

    def __init__(self, parent=None):
        super(PulseWindow, self).__init__(parent=parent)
        self.setObjectName(self.OBJECT_NAME)
        self.setProperty('saveWindowPref', True)

    def show(self):
        """
        Show the PulseWindow.
        """
        super(PulseWindow, self).show(dockable=True, retain=False)
