
from Qt import QtCore, QtWidgets, QtGui
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


__all__ = [
    'PulseWindow',
]


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
        workspaceControlName = cls.OBJECT_NAME + 'WorkspaceControl'
        if cmds.workspaceControl(workspaceControlName, q=True, ex=True):
            result = True
        if cmds.workspaceControl(workspaceControlName, q=True, ex=True):
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
        workspaceControlName = cls.OBJECT_NAME + 'WorkspaceControl'
        # close and delete an existing workspace control
        if cmds.workspaceControl(workspaceControlName, q=True, ex=True):
            cmds.workspaceControl(workspaceControlName, e=True, close=True)
            result = True
        if cmds.workspaceControl(workspaceControlName, q=True, ex=True):
            cmds.deleteUI(workspaceControlName, control=True)
            result = True
        if cmds.window(cls.OBJECT_NAME, q=True, ex=True):
            cmds.deleteUI(cls.OBJECT_NAME, window=True)
            result = True
        return result

    def __init__(self, parent=None):
        super(PulseWindow, self).__init__(parent=parent)
        self.setObjectName(self.OBJECT_NAME)
        self.setProperty('saveWindowPref', True)

    def show(self):
        """
        Show the PulseWindow.
        """
        super(PulseWindow, self).show(dockable=True, retain=False)
