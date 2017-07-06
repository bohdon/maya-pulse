
from Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm

import pulse

# the title of the window
WINDOW_TITLE = 'PulseActionTree'
# the name of the action tree maya window
WINDOW_OBJECT = 'pulseActionTreeWindow'


def _mainWindow():
    """
    Return Maya's main Qt window
    """
    for obj in QtWidgets.qApp.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')

def _deleteUI():
    """
    Delete existing ActionTreeWindow
    """
    if pm.cmds.window(WINDOW_OBJECT, q=True, exists=True):
        pm.cmds.deleteUI(WINDOW_OBJECT)
    if pm.cmds.dockControl('MayaWindow|' + WINDOW_TITLE, q=True, ex=True):
        pm.cmds.deleteUI('MayaWindow|' + WINDOW_TITLE)

def show(dock=False):
    """
    Show the ActionTreeWindow
    """
    _deleteUI()

    window = ActionTreeWindow(parent=_mainWindow())

    if not dock:
        window.show()
    else:
        allowedAreas = ['right', 'left']
        pm.cmds.dockControl(WINDOW_TITLE, label=WINDOW_TITLE, area='left',
                         content=WINDOW_OBJECT, allowedArea=allowedAreas)

    return window



class ActionTreeItem(object):
    """
    A BuildItem wrapper class that provides a consistent
    interface for using BuildItems in an ActionTreeItemModel
    """

    def __init__(self, buildItem, parent=None):
        # the parent ActionTreeItem of this item
        self._parent = parent
        # the child ActionTreeItems of this item
        self.children = []
        # the actual BuildItem of this model item
        self.buildItem = buildItem

    def appendChild(self, item):
        self.children.append(item)

    def columnCount(self):
        return 1

    def childCount(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def parent(self):
        return self._parent

    def row(self):
        if self._parent:
            return self._parent.children.index(self)
        return 0

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return self.buildItem.getDisplayName()
        elif role == QtCore.Qt.DecorationRole:
            iconFile = self.buildItem.getIconFile()
            if iconFile:
                return QtGui.QIcon(iconFile)





class ActionTreeItemModel(QtCore.QAbstractItemModel):

    def __init__(self, parent=None, blueprint=None):
        super(ActionTreeItemModel, self).__init__(parent=parent)
        # the blueprint to use for this models data
        self.blueprint = blueprint
        self.rootItem = ActionTreeItem(self.blueprint.rootGroup)
        self.updateModelItems(self.rootItem)

    def updateModelItems(self, parent):
        if isinstance(parent.buildItem, pulse.BuildGroup):
            for childBuildItem in parent.buildItem.children:
                child = ActionTreeItem(childBuildItem, parent)
                parent.appendChild(child)
                self.updateModelItems(child)

    def index(self, row, column, parent): # override
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if parent.isValid():
            parentItem = parent.internalPointer()
        else:
            parentItem = self.rootItem

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def columnCount(self, parent): # override
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def rowCount(self, parent): # override
        if parent.column() > 0:
            return 0

        if parent.isValid():
            parentItem = parent.internalPointer()
        else:
            parentItem = self.rootItem

        return parentItem.childCount()

    def parent(self, index): # override
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def data(self, index, role=QtCore.Qt.DisplayRole): # override
        if not index.isValid():
            return
        
        item = index.internalPointer()
        return item.data(index.column(), role)



class ActionTreeWidget(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super(ActionTreeWidget, self).__init__(parent=parent)
        # build the ui
        self.setupUi(self)
        # connect buttons
        self.refreshBtn.clicked.connect(self.refreshTreeData)
        # perform initial refresh
        self.refreshTreeData()

    def refreshTreeData(self):
        model = ActionTreeItemModel(self, pulse.Blueprint.fromDefaultNode())
        self.treeView.setModel(model)

    def setupUi(self, parent):
        lay = QtWidgets.QVBoxLayout(parent)

        self.refreshBtn = QtWidgets.QPushButton()
        self.refreshBtn.setText('Refresh')
        lay.addWidget(self.refreshBtn)

        self.treeView = QtWidgets.QTreeView(parent)
        self.treeView.setHeaderHidden(True)
        self.treeView.setDragEnabled(True)
        self.treeView.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView.setIndentation(14)
        lay.addWidget(self.treeView)



class ActionTreeWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(ActionTreeWindow, self).__init__(parent=parent)

        # set object name and window title for maya to find
        self.setObjectName(WINDOW_OBJECT)
        self.setWindowTitle(WINDOW_TITLE)

        self.setWindowFlags(QtCore.Qt.Window)
        self.setProperty("saveWindowPref", True)

        self.actionTree = ActionTreeWidget(self)
        self.setCentralWidget(self.actionTree)
