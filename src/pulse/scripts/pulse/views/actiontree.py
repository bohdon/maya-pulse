
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymetanode as meta

import pulse
from .core import PulseWindow


__all__ = [
    'ActionButtonsWidget',
    'ActionTreeItem',
    'ActionTreeItemModel',
    'ActionTreeSelectionModel',
    'ActionTreeWidget',
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

    INSTANCE = None

    @classmethod
    def getSharedModel(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = cls()
        return cls.INSTANCE

    def __init__(self, parent=None):
        super(ActionTreeItemModel, self).__init__(parent=parent)
        # load the blueprint from the scene
        self.blueprint = pulse.Blueprint()
        self.reloadBlueprint()

    def reloadBlueprint(self):
        if not self.blueprint.loadFromDefaultNode():
            # no blueprint, reset to new instance
            self.blueprint = pulse.Blueprint()
        self.rootItem = ActionTreeItem(self.blueprint.rootGroup)
        self.modelReset.emit()

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
            return QtCore.Qt.ItemIsDropEnabled

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
        except Exception as e:
            print(e)
            return False
        else:
            newBuildItems = [pulse.BuildItem.create(itemData) for itemData in itemDataList]
            return self.insertBuildItems(row, newBuildItems, parent)



class ActionTreeSelectionModel(QtCore.QItemSelectionModel):

    INSTANCE = None

    @classmethod
    def getSharedModel(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = cls(ActionTreeItemModel.getSharedModel())
            cls.INSTANCE.asdf = 1234
        return cls.INSTANCE

    def getSelectedGroups(self):
        """
        Return the currently selected BuildGroup indexes
        """
        indexes = self.selectedIndexes()
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




class ActionTreeWidget(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super(ActionTreeWidget, self).__init__(parent=parent)
        # get shared models
        self.model = ActionTreeItemModel.getSharedModel()
        self.selectionModel = ActionTreeSelectionModel.getSharedModel()
        # build the ui
        self.setupUi(self)
        # connect signals
        self.model.modelReset.connect(self.onBlueprintLoaded)

    def onBlueprintLoaded(self):
        self.treeView.expandAll()

    def eventFilter(self, widget, event):
        if widget is self.treeView:
            if event.type() == QtCore.QEvent.KeyPress:
                key = event.key()
                if key == QtCore.Qt.Key_Delete:
                    self.deleteSelectedItems()
                    return True
        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        self.treeView = QtWidgets.QTreeView(parent)
        self.treeView.setHeaderHidden(True)
        self.treeView.setDragEnabled(True)
        self.treeView.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)
        self.treeView.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView.setIndentation(14)
        self.treeView.installEventFilter(self)
        self.treeView.setModel(self.model)
        self.treeView.setSelectionModel(self.selectionModel)
        self.treeView.expandAll()
        layout.addWidget(self.treeView)

    def deleteSelectedItems(self):
        wasChanged = False
        while True:
            indexes = self.selectionModel.selectedIndexes()
            if not indexes:
                break
            if not self.model.removeRow(indexes[0].row(), indexes[0].parent()):
                break
            wasChanged = True
        if wasChanged:
            self.model.blueprint.saveToDefaultNode()




class ActionButtonsWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ActionButtonsWidget, self).__init__(parent=parent)

        self.model = ActionTreeItemModel.getSharedModel()
        self.selectionModel = ActionTreeSelectionModel.getSharedModel()
        self.setupUi(self)
    
    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
    
        grpBtn = QtWidgets.QPushButton(parent)
        grpBtn.setText("New Group")
        grpBtn.clicked.connect(self.createBuildGroup)
        layout.addWidget(grpBtn)

        searchField = QtWidgets.QLineEdit(parent)
        searchField.setPlaceholderText("Search")
        layout.addWidget(searchField)

        tabScrollWidget = QtWidgets.QWidget(parent)
        tabScroll = QtWidgets.QScrollArea(parent)
        tabScroll.setFrameShape(QtWidgets.QScrollArea.NoFrame)
        tabScroll.setWidgetResizable(True)
        tabScroll.setWidget(tabScrollWidget)

        self.setupContentUi(tabScrollWidget)

        layout.addWidget(tabScroll)

    def setupContentUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        
        # make button for each action
        registeredActions = pulse.getRegisteredActions().values()
        categories = list(set([ac.config.get('category', 'Default') for ac in registeredActions]))
        categoryLayouts = {}

        # create category layouts
        for i, cat in enumerate(sorted(categories)):
            # add category layout
            catLay = QtWidgets.QVBoxLayout(parent)
            catLay.setSpacing(4)
            layout.addLayout(catLay)
            categoryLayouts[cat] = catLay
            # add label
            label = self.createLabel(parent, cat)
            catLay.addWidget(label)

        for actionClass in registeredActions:
            cat = actionClass.config.get('category', 'Default')
            color = self.getActionColor(actionClass)
            btn = QtWidgets.QPushButton(parent)
            btn.setText(actionClass.config['displayName'])
            btn.setStyleSheet('background-color:rgba({0}, {1}, {2}, 30)'.format(*color))
            btn.setMinimumHeight(22)
            cmd = lambda x=actionClass.getTypeName(): self.createBuildAction(x)
            btn.clicked.connect(cmd)
            categoryLayouts[cat].addWidget(btn)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)
    
    def createLabel(self, parent, text):
        label = QtWidgets.QLabel(parent)
        label.setText(text)
        label.setMinimumHeight(20)
        label.setContentsMargins(10, 2, 2, 2)
        label.setStyleSheet('background-color: rgba(0, 0, 0, 40); border-radius: 2px')
        return label
    
    def getActionColor(self, actionClass):
        color = actionClass.config.get('color', [1, 1, 1])
        if color:
            return [int(c * 255) for c in color]
        else:
            return [255, 255, 255]

    def onActionClicked(self, typeName):
        self.model
        self.clicked.emit(typeName)

    def createBuildGroup(self):
        if not self.model.blueprint:
            return

        grpIndexes = self.selectionModel.getSelectedGroups()
        gc = pulse.getBuildItemClass('BuildGroup')
        for grpIndex in grpIndexes:
            grp = gc()
            self.model.insertBuildItems(0, [grp], grpIndex)
        self.model.blueprint.saveToDefaultNode()

    def createBuildAction(self, typeName):
        if not self.model.blueprint:
            return

        grpIndexes = self.selectionModel.getSelectedGroups()
        ac = pulse.getActionClass(typeName)
        newIndexes = []
        for grpIndex in grpIndexes:
            action = ac()
            if self.model.insertBuildItems(0, [action], grpIndex):
                newIndexes.append(self.model.index(0, 0, grpIndex))
        # select new items
        self.selectionModel.clearSelection()
        for index in newIndexes:
            self.selectionModel.select(index, QtCore.QItemSelectionModel.Select)
        self.model.blueprint.saveToDefaultNode()




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
        layout.addWidget(self.actionButtons)

        layout.setStretch(layout.indexOf(self.actionTree), 2)
        layout.setStretch(layout.indexOf(self.actionButtons), 1)

