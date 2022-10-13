"""
Palette for browsing actions that can be added to a blueprint.
"""

import logging
import os
from functools import partial

import maya.cmds as cmds

from ..vendor.Qt import QtCore, QtWidgets
from ..buildItems import getRegisteredActionConfigs
from .core import BlueprintUIModel, PulseWindow

from .gen.action_palette import Ui_ActionPalette

LOG = logging.getLogger(__name__)
LOG_LEVEL_KEY = 'PYLOG_%s' % LOG.name.split('.')[0].upper()
LOG.setLevel(os.environ.get(LOG_LEVEL_KEY, 'INFO').upper())


class ActionPalette(QtWidgets.QWidget):
    """
    Provides UI for creating any BuildAction. One button is created
    for each BuildAction, and they are grouped by category. Also
    includes a search field for filtering the list of actions.
    """

    def __init__(self, parent=None):
        super(ActionPalette, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.blueprintModel.readOnlyChanged.connect(self._onReadOnlyChanged)
        self.model = self.blueprintModel.buildStepTreeModel
        self.selectionModel = self.blueprintModel.buildStepSelectionModel

        self.ui = Ui_ActionPalette()
        self.ui.setupUi(self)

        self.setupActionsUi(self.ui.scroll_area_widget, self.ui.actions_layout)

        self.ui.group_btn.clicked.connect(self.createGroup)

        self._onReadOnlyChanged(self.blueprintModel.isReadOnly())

    def setupActionsUi(self, parent, layout):
        """
        Build buttons for creating each action.
        """

        allActionConfigs = getRegisteredActionConfigs()

        # make button for each action
        categories = [c.get('category', 'Default') for c in allActionConfigs]
        categories = list(set(categories))
        categoryLayouts = {}

        # create category layouts
        for cat in sorted(categories):
            # add category layout
            catLay = QtWidgets.QVBoxLayout(parent)
            catLay.setSpacing(2)
            layout.addLayout(catLay)
            categoryLayouts[cat] = catLay
            # add label
            label = QtWidgets.QLabel(parent)
            label.setText(cat)
            label.setProperty('cssClasses', 'section-title')
            catLay.addWidget(label)

        for actionConfig in allActionConfigs:
            actionId = actionConfig['id']
            actionCategory = actionConfig.get('category', 'Default')
            color = self.getActionColor(actionConfig)
            btn = QtWidgets.QPushButton(parent)
            btn.setText(actionConfig['displayName'])
            btn.setStyleSheet('background-color:rgba({0}, {1}, {2}, 30)'.format(*color))
            btn.clicked.connect(partial(self.createAction, actionId))
            categoryLayouts[actionCategory].addWidget(btn)

        spacer = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        layout.addItem(spacer)

    @staticmethod
    def getActionColor(actionConfig):
        color = actionConfig.get('color', [1, 1, 1])
        if color:
            return [int(c * 255) for c in color]
        else:
            return [255, 255, 255]

    def _onReadOnlyChanged(self, isReadOnly):
        self.ui.group_btn.setEnabled(not isReadOnly)
        self.ui.scroll_area_widget.setEnabled(not isReadOnly)

    def _onActionClicked(self, typeName):
        self.clicked.emit(typeName)

    def createStepsForSelection(self, stepData=None):
        """
        Create new BuildSteps in the hierarchy at the
        current selection and return the new step paths.

        Args:
            stepData (str): A string representation of serialized
                BuildStep data used to create the new steps
        """
        if self.blueprintModel.isReadOnly():
            LOG.warning('cannot create steps, blueprint is read only')
            return

        LOG.debug('creating new steps at selection: %s', stepData)

        selIndexes = self.selectionModel.selectedIndexes()
        if not selIndexes:
            selIndexes = [QtCore.QModelIndex()]

        model = self.selectionModel.model()

        def getParentAndInsertIndex(index):
            step = model.stepForIndex(index)
            LOG.debug('step: %s', step)
            if step.canHaveChildren:
                LOG.debug('inserting at num children: %d', step.numChildren())
                return step, step.numChildren()
            else:
                LOG.debug('inserting at selected + 1: %d', index.row() + 1)
                return step.parent, index.row() + 1

        newPaths = []
        for index in selIndexes:
            parentStep, insertIndex = getParentAndInsertIndex(index)
            parentPath = parentStep.getFullPath() if parentStep else None
            if not parentPath:
                parentPath = ''
            if not stepData:
                stepData = ''
            newStepPath = cmds.pulseCreateStep(
                parentPath, insertIndex, stepData)
            if newStepPath:
                # TODO: remove this if/when plugin command only returns single string
                newStepPath = newStepPath[0]
                newPaths.append(newStepPath)
            # if self.model.insertRows(insertIndex, 1, parentIndex):
            #     newIndex = self.model.index(insertIndex, 0, parentIndex)
            #     newPaths.append(newIndex)

        return newPaths

    def createGroup(self):
        if self.blueprintModel.isReadOnly():
            LOG.warning("Cannot create group, blueprint is read-only")
            return
        LOG.debug('create_group')
        newPaths = self.createStepsForSelection()
        self.selectionModel.setSelectedItemPaths(newPaths)

    def createAction(self, actionId):
        if self.blueprintModel.isReadOnly():
            LOG.warning("Cannot create action, blueprint is read-only")
            return
        LOG.debug('create_action: %s', actionId)
        stepData = "{'action':{'id':'%s'}}" % actionId
        newPaths = self.createStepsForSelection(stepData=stepData)
        self.selectionModel.setSelectedItemPaths(newPaths)


class ActionPaletteWindow(PulseWindow):
    OBJECT_NAME = 'pulseActionPaletteWindow'
    WINDOW_MODULE = 'pulse.ui.actionpalette'
    WINDOW_TITLE = 'Pulse Action Palette'
    WIDGET_CLASS = ActionPalette
