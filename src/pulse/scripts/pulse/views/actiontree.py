
from Qt import QtCore, QtWidgets, QtGui
import pymetanode as meta

import pulse
from pulse.views.core import PulseWindow


__all__ = [
    'ActionTreeItem',
    'ActionTreeItemModel',
    'ActionTreeWidget',
    'ActionButtonsWidget',
    'ActionTreeWindow',
]


class ActionTreeItem(object):
    """
    A BuildItem wrapper class that provides a consistent
    interface for using BuildItems in an ActionTreeItemModel
    """

    def __init__(self, buildItem, parent=None):
        # the parent ActionTreeItem of this item
        self._parent = parent
        # children are lazily loaded when needed
        self._children = None
        # the actual BuildItem of this model item
        self.buildItem = buildItem

    @property
    def children(self):
        if self._children is None:
            if self.isGroup():
                self._children = [ActionTreeItem(c, self) for c in self.buildItem.children]
            else:
                self._children = []
        return self._children

    def isGroup(self):
        return isinstance(self.buildItem, pulse.BuildGroup)

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

    def insertChildren(self, position, childBuildItems):
        if not self.isGroup():
            return False

        if position < 0:
            position = self.childCount()

        for childBuildItem in childBuildItems:
            self.buildItem.insertChild(position, childBuildItem)
            self.children.insert(position, ActionTreeItem(childBuildItem, self))

        return True

    def removeChildren(self, position, count):
        if not self.isGroup():
            return False

        if position < 0 or position + count > self.childCount():
            return False

        for row in range(count):
            self.buildItem.removeChildAt(position)
            del self.children[position]

        return True

    def setData(self, column, value):
        if not self.isGroup():
            return False

        self.buildItem.displayName = value

        return True


    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if isinstance(self.buildItem, pulse.BuildGroup):
                return '{0} ({1})'.format(self.buildItem.getDisplayName(), self.buildItem.getChildCount())
            elif isinstance(self.buildItem, pulse.BatchBuildAction):
                return '{0} (x{1})'.format(self.buildItem.getDisplayName(), self.buildItem.getActionCount())
            else:
                return self.buildItem.getDisplayName()

        elif role == QtCore.Qt.EditRole:
            return self.buildItem.getDisplayName()

        elif role == QtCore.Qt.DecorationRole:
            iconFile = self.buildItem.getIconFile()
            if iconFile:
                return QtGui.QIcon(iconFile)

        elif role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(0, 20)

        elif role == QtCore.Qt.ForegroundRole:
            color = self.buildItem.getColor()
            if color:
                return QtGui.QColor(*[c * 255 for c in color])




class ActionTreeItemModel(QtCore.QAbstractItemModel):

    def __init__(self, parent=None, blueprint=None):
        super(ActionTreeItemModel, self).__init__(parent=parent)
        # the blueprint to use for this models data
        self.blueprint = blueprint
        self.rootItem = ActionTreeItem(self.blueprint.rootGroup)

    def getItem(self, index):
        """
        Return the ActionTreeItem for a QModelIndex
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def index(self, row, column, parent): # override
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parentItem = self.getItem(parent)

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def flags(self, index):
        if not index.isValid():
            return 0

        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled
        item = self.getItem(index)
        if item.isGroup():
            flags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled
        return flags

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def columnCount(self, parent): # override
        return self.rootItem.columnCount()

    def rowCount(self, parent=QtCore.QModelIndex()): # override
        return self.getItem(parent).childCount()

    def parent(self, index): # override
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        raise RuntimeError("Cannot insert rows without data, use insertBuildItems instead")

    def insertBuildItems(self, position, childBuildItems, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)

        self.beginInsertRows(parent, position, position + len(childBuildItems) - 1)
        success = parentItem.insertChildren(position, childBuildItems)
        self.endInsertRows()

        return success

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + rows - 1)
        success = parentItem.removeChildren(position, rows)
        self.endRemoveRows()

        return success

    def data(self, index, role=QtCore.Qt.DisplayRole): # override
        if not index.isValid():
            return
        
        item = index.internalPointer()
        return item.data(index.column(), role)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result

    def mimeTypes(self):
        return ['text/plain']

    def mimeData(self, indexes):
        result = QtCore.QMimeData()
        itemDataList = [index.internalPointer().buildItem.serialize() for index in indexes]
        datastr = meta.encodeMetaData(itemDataList)
        result.setData('text/plain', datastr)
        return result

    def dropMimeData(self, data, action, row, column, parent):
        try:
            itemDataList = meta.decodeMetaData(str(data.data('text/plain')))
        except:
            return False
        newBuildItems = [pulse.BuildItem.create(itemData) for itemData in itemDataList]
        return self.insertBuildItems(row, newBuildItems, parent)




class ActionTreeWidget(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super(ActionTreeWidget, self).__init__(parent=parent)
        self.blueprint = None
        # build the ui
        self.setupUi(self)
        # connect buttons
        self.refreshBtn.clicked.connect(self.reloadBlueprint)
        # update tree model
        self.reloadBlueprint()

    def eventFilter(self, widget, event):
        if widget is self.treeView:
            if event.type() == QtCore.QEvent.KeyPress:
                key = event.key()
                if key == QtCore.Qt.Key_Delete:
                    self.deleteSelectedItems()
                    return True
        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def reloadBlueprint(self):
        self.blueprint = pulse.Blueprint.fromDefaultNode()
        if self.blueprint:
            self.model = ActionTreeItemModel(self, self.blueprint)
        else:
            self.model = None

        self.treeView.setModel(self.model)
        self.treeView.expandAll()

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
        self.treeView.installEventFilter(self)
        lay.addWidget(self.treeView)

    def deleteSelectedItems(self):
        if not self.blueprint:
            return

        wasChanged = False
        while True:
            indexes = self.treeView.selectionModel().selectedIndexes()
            if not indexes:
                break
            if not self.model.removeRow(indexes[0].row(), indexes[0].parent()):
                break
            wasChanged = True
        if wasChanged:
            self.blueprint.saveToDefaultNode()

    def getSelectedGroups(self):
        """
        Return the currently selected BuildGroup indexes
        """
        indexes = self.treeView.selectionModel().selectedIndexes()
        grps = []
        for index in indexes:
            item = index.internalPointer()
            if item.isGroup():
                grps.append(index)
            else:
                grps.append(index.parent())
        return list(set(grps))


    def getSelectedAction(self):
        """
        Return the currently selected BuildAction, if any.
        """
        pass


class ActionButtonsWidget(QtWidgets.QWidget):

    clicked = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ActionButtonsWidget, self).__init__(parent=parent)

        lay = QtWidgets.QVBoxLayout(self)

        registeredActions = pulse.getRegisteredActions().values()
        categories = list(set([ac.config.get('category', 'Default') for ac in registeredActions]))

        tabWidget = QtWidgets.QTabWidget(self)
        tabWidget.setObjectName("tabWidget")

        tabWidgets = {}

        for i, cat in enumerate(categories):
            tab = QtWidgets.QWidget()
            tabOuterLay = QtWidgets.QVBoxLayout(tab)
            tabScroll = QtWidgets.QScrollArea(tab)
            tabScroll.setWidgetResizable(True)
            tabScrollWidget = QtWidgets.QWidget(tab)
            tabLay = QtWidgets.QVBoxLayout(tabScrollWidget)
            tabWidgets[cat] = tabScrollWidget
            # setup relationships
            tabScroll.setWidget(tabScrollWidget)
            tabOuterLay.addWidget(tabScroll)
            tabWidget.addTab(tab, "")
            # set tab label
            tabWidget.setTabText(i, cat)

        lay.addWidget(tabWidget)

        for actionClass in registeredActions:
            cat = actionClass.config.get('category', 'Default')
            btn = QtWidgets.QPushButton()
            btn.setText(actionClass.config['displayName'])
            cmd = lambda x=actionClass.getTypeName(): self.onActionClicked(x)
            btn.clicked.connect(cmd)
            tabWidgets[cat].layout().addWidget(btn)

        for cat in categories:
            spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            tabWidgets[cat].layout().addItem(spacer)

    def onActionClicked(self, typeName):
        self.clicked.emit(typeName)




class ActionTreeWindow(PulseWindow):

    OBJECT_NAME = 'pulseActionTreeWindow'

    def __init__(self, parent=None):
        super(ActionTreeWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Tree')

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)

        layout = QtWidgets.QVBoxLayout(self)
        widget.setLayout(layout)

        self.actionTree = ActionTreeWidget(self)
        layout.addWidget(self.actionTree)

        self.actionButtons = ActionButtonsWidget(self)
        self.actionButtons.clicked.connect(self.addBuildAction)
        layout.addWidget(self.actionButtons)

        grpBtn = QtWidgets.QPushButton(self)
        grpBtn.setText("New Group")
        grpBtn.clicked.connect(self.addBuildGroup)
        layout.addWidget(grpBtn)

        layout.setStretch(layout.indexOf(self.actionTree), 2)
        layout.setStretch(layout.indexOf(self.actionButtons), 1)


    def addBuildGroup(self):
        if not self.actionTree.blueprint:
            return

        grpIndexes = self.actionTree.getSelectedGroups()
        gc = pulse.getBuildItemClass('BuildGroup')
        for grpIndex in grpIndexes:
            grp = gc()
            self.actionTree.model.insertBuildItems(0, [grp], grpIndex)
        self.actionTree.blueprint.saveToDefaultNode()

    def addBuildAction(self, typeName):
        if not self.actionTree.blueprint:
            return

        grpIndexes = self.actionTree.getSelectedGroups()
        ac = pulse.getActionClass(typeName)
        for grpIndex in grpIndexes:
            action = ac()
            self.actionTree.model.insertBuildItems(0, [action], grpIndex)
        self.actionTree.blueprint.saveToDefaultNode()


