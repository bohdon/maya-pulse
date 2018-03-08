
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse
from .core import PulseWindow
from .core import BlueprintUIModel, BuildItemTreeModel, BuildItemSelectionModel


__all__ = [
    'ActionButtonsWidget',
    'ActionTreeWidget',
    'ActionTreeWindow',
]



class ActionTreeWidget(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super(ActionTreeWidget, self).__init__(parent=parent)

        # get shared models
        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildItemTreeModel
        self.selectionModel = self.blueprintModel.buildItemSelectionModel
        
        self.setupUi(self)

        # connect signals
        self.model.modelReset.connect(self.onModelReset)
    
    def showEvent(self, event):
        super(ActionTreeWidget, self).showEvent(event)
        self.blueprintModel.addSubscriber(self)

    def hideEvent(self, event):
        super(ActionTreeWidget, self).hideEvent(event)
        self.blueprintModel.removeSubscriber(self)

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
    
    def onModelReset(self):
        self.treeView.expandAll()

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
            self.blueprintModel.save()




class ActionButtonsWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ActionButtonsWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildItemTreeModel
        self.selectionModel = self.blueprintModel.buildItemSelectionModel
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
        self.clicked.emit(typeName)

    def createBuildGroup(self):
        if self.blueprintModel.isReadOnly():
            return

        grpIndexes = self.selectionModel.getSelectedGroups()
        gc = pulse.getBuildItemClass('BuildGroup')
        for grpIndex in grpIndexes:
            grp = gc()
            self.model.insertBuildItems(0, [grp], grpIndex)
        self.blueprintModel.save()

    def createBuildAction(self, typeName):
        if self.blueprintModel.isReadOnly():
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
        self.blueprintModel.save()




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

