
import pulse
from pulse.vendor.Qt import QtCore, QtWidgets
from .core import PulseWindow
from .core import BlueprintUIModel


__all__ = [
    'ActionPaletteWidget',
    'ActionTreeWidget',
    'ActionTreeWindow',
]


class ActionTreeWidget(QtWidgets.QWidget):
    """
    A tree view that displays all BuildActions in a Blueprint.
    Items can be selected, and the shared selection model
    can then be used to display info about selected BuildActions
    in other UI.
    """

    def __init__(self, parent=None):
        super(ActionTreeWidget, self).__init__(parent=parent)

        # get shared models
        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel
        self.selectionModel = self.blueprintModel.buildStepSelectionModel

        self.setupUi(self)

        # connect signals
        self.model.modelReset.connect(self.onModelReset)

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
        self.treeView.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.treeView.setDefaultDropAction(
            QtCore.Qt.DropAction.MoveAction)
        self.treeView.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView.setIndentation(14)
        self.treeView.installEventFilter(self)
        self.treeView.setModel(self.model)
        self.treeView.setSelectionModel(self.selectionModel)
        self.treeView.expandAll()
        layout.addWidget(self.treeView)

    def onModelReset(self):
        self.treeView.expandAll()

    def deleteSelectedItems(self):
        while True:
            indexes = self.selectionModel.selectedIndexes()
            if not indexes:
                break
            if not self.model.removeRow(indexes[0].row(), indexes[0].parent()):
                break


class ActionPaletteWidget(QtWidgets.QWidget):
    """
    Provides UI for creating any BuildAction. One button is created
    for each BuildAction, and they are grouped by category. Also
    includes a search field for filtering the list of actions.
    """

    def __init__(self, parent=None):
        super(ActionPaletteWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel
        self.selectionModel = self.blueprintModel.buildStepSelectionModel
        self.setupUi(self)

    def setupUi(self, parent):
        """ Build the UI """
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
        """ Build the action buttons UI """
        layout = QtWidgets.QVBoxLayout(parent)

        allActionConfigs = pulse.getRegisteredActionConfigs()

        # make button for each action
        categories = [c.get('category', 'Default') for c in allActionConfigs]
        categories = list(set(categories))
        categoryLayouts = {}

        # create category layouts
        for cat in sorted(categories):
            # add category layout
            catLay = QtWidgets.QVBoxLayout(parent)
            catLay.setSpacing(4)
            layout.addLayout(catLay)
            categoryLayouts[cat] = catLay
            # add label
            label = self.createLabel(parent, cat)
            catLay.addWidget(label)

        for actionConfig in allActionConfigs:
            actionId = actionConfig['id']
            actionCategory = actionConfig.get('category', 'Default')
            color = self.getActionColor(actionConfig)
            btn = QtWidgets.QPushButton(parent)
            btn.setText(actionConfig['displayName'])
            btn.setStyleSheet(
                'background-color:rgba({0}, {1}, {2}, 30)'.format(*color))
            btn.setMinimumHeight(22)
            cmd = lambda x=actionId: self.createBuildAction(x)
            btn.clicked.connect(cmd)
            categoryLayouts[actionCategory].addWidget(btn)

        spacer = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

    def createLabel(self, parent, text):
        label = QtWidgets.QLabel(parent)
        label.setText(text)
        label.setMinimumHeight(20)
        label.setContentsMargins(10, 2, 2, 2)
        label.setStyleSheet(
            'background-color: rgba(0, 0, 0, 40); border-radius: 2px')
        return label

    def getActionColor(self, actionConfig):
        color = actionConfig.get('color', [1, 1, 1])
        if color:
            return [int(c * 255) for c in color]
        else:
            return [255, 255, 255]

    def onActionClicked(self, typeName):
        self.clicked.emit(typeName)

    def createStepsForSelection(self):
        """
        Create new BuildSteps in the hierarchy at the
        current selection and return the new model indexes.
        """
        if self.blueprintModel.isReadOnly():
            return

        selIndexes = self.selectionModel.selectedIndexes()
        if not selIndexes:
            selIndexes = [QtCore.QModelIndex()]

        model = self.selectionModel.model()

        def getParentAndInsertIndex(index):
            step = model.stepForIndex(index)
            print('step', step)
            if step.canHaveChildren:
                print('inserting at num children')
                return index, step.numChildren()
            else:
                print('inserting at selected + 1')
                return model.parent(index), index.row() + 1

        newIndexes = []
        for index in selIndexes:
            parentIndex, insertIndex = getParentAndInsertIndex(index)
            if self.model.insertRows(insertIndex, 1, parentIndex):
                newIndex = self.model.index(insertIndex, 0, parentIndex)
                newIndexes.append(newIndex)

        return newIndexes

    def createBuildGroup(self):
        if self.blueprintModel.isReadOnly():
            return

        newIndexes = self.createStepsForSelection()
        model = self.selectionModel.model()

        # update steps with correct action id and select them
        self.selectionModel.clearSelection()
        for index in newIndexes:
            step = model.stepForIndex(index)
            if step:
                step.setName('New Step')
                model.dataChanged.emit(index, index, [])
            self.selectionModel.select(
                index, QtCore.QItemSelectionModel.Select)

    def createBuildAction(self, actionId):
        if self.blueprintModel.isReadOnly():
            return

        newIndexes = self.createStepsForSelection()
        model = self.selectionModel.model()

        # update steps with correct action id and select them
        self.selectionModel.clearSelection()
        for index in newIndexes:
            step = model.stepForIndex(index)
            if step:
                actionProxy = pulse.BuildActionProxy(actionId)
                step.setActionProxy(actionProxy)
            model.dataChanged.emit(index, index, [])
            self.selectionModel.select(
                index, QtCore.QItemSelectionModel.Select)


class ActionTreeWindow(PulseWindow):
    """
    A standalone window that contains an ActionTreeWidget
    and an ActionPaletteWidget.
    """

    OBJECT_NAME = 'pulseActionTreeWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.actiontree'

    def __init__(self, parent=None):
        super(ActionTreeWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Tree')

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.actionTree = ActionTreeWidget(self)
        layout.addWidget(self.actionTree)

        self.actionPalette = ActionPaletteWidget(self)
        layout.addWidget(self.actionPalette)

        layout.setStretch(layout.indexOf(self.actionTree), 2)
        layout.setStretch(layout.indexOf(self.actionPalette), 1)
