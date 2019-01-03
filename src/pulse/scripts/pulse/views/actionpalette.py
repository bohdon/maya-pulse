
import pulse
from pulse.vendor.Qt import QtCore, QtWidgets
from .core import BlueprintUIModel
from .utils import createHeaderLabel

__all__ = [
    'ActionPaletteWidget',
]


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
            label = createHeaderLabel(parent, cat)
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
