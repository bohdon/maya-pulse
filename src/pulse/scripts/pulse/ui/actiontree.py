"""
Tree widget for displaying the build step hierarchy of a blueprint.
"""

import logging
from functools import partial
from typing import Optional, Dict, List

import maya.cmds as cmds

from ..vendor.Qt import QtCore, QtWidgets, QtGui
from ..serializer import serialize_attr_value
from ..build_items import BuildStep, BuildActionRegistry, BuildActionSpec, BuildActionAttribute
from .. import sym
from .core import BlueprintUIModel
from .core import PulseWindow
from .gen.action_tree import Ui_ActionTree

LOG = logging.getLogger(__name__)


class ActionTreeStyledItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ActionTreeStyledItemDelegate, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super(ActionTreeStyledItemDelegate, self).paint(painter, option, index)


class ActionTreeView(QtWidgets.QTreeView):
    """
    A tree view for displaying BuildActions in a Blueprint
    """

    def __init__(self, blueprintModel=None, parent=None):
        super().__init__(parent=parent)

        self.blueprintModel = blueprintModel

        self.setItemDelegate(ActionTreeStyledItemDelegate(parent))
        self.setHeaderHidden(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setIndentation(14)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            self.deleteSelectedItems()
            return True

        elif key == QtCore.Qt.Key_D:
            self.toggleSelectedItemsDisabled()
            return True

        elif key == QtCore.Qt.Key_M:
            self.mirrorSelectedItems()
            return True

        return super().keyPressEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        # don't perform selection changes on middle mouse press
        if event.buttons() & QtCore.Qt.MiddleButton:
            return True

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        # start dragging when using middle mouse
        if event.buttons() & QtCore.Qt.MiddleButton:
            self.startDrag(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction)
            return True

        return super().mouseMoveEvent(event)

    def deleteSelectedItems(self):
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps: List[BuildStep] = []
        for index in indexes:
            step: BuildStep = self.model().stepForIndex(index)
            if step:
                steps.append(step)
        steps = BuildStep.get_topmost_steps(steps)

        paths = []
        for step in steps:
            path = step.get_full_path()
            print(step, path)
            if path:
                paths.append(path)

        cmds.undoInfo(openChunk=True, chunkName="Delete Pulse Actions")
        for path in paths:
            cmds.pulseDeleteStep(path)
        cmds.undoInfo(closeChunk=True)

    def toggleSelectedItemsDisabled(self):
        """
        Toggle the disabled state of the selected items.
        If item disable states are mismatched, will disable all items.
        """
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps = []
        for index in indexes:
            step = self.model().stepForIndex(index)
            if step:
                steps.append((index, step))

        all_disabled = all([s.isDisabled for i, s in steps])
        newDisabled = False if all_disabled else True
        for index, step in steps:
            self.model().setData(index, newDisabled, QtCore.Qt.CheckStateRole)

    def mirrorSelectedItems(self):
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps: List[BuildStep] = []
        for index in indexes:
            step: BuildStep = self.model().stepForIndex(index)
            if step:
                steps.append(step)

        is_all_mirrored = all([step.action_proxy.is_mirrored for step in steps if step.is_action()])
        mirror_value = True if not is_all_mirrored else False
        for step in steps:
            if step.is_action():
                cmds.pulseSetIsActionMirrored(step.get_full_path(), mirror_value)


class ActionTree(QtWidgets.QWidget):
    """
    A widget that displays all Build Actions in a Blueprint.
    Items can be selected, and the shared selection model can then be used to
    display info about selected BuildActions in other UI.
    """

    def __init__(self, parent=None):
        super(ActionTree, self).__init__(parent=parent)

        # get shared models
        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel
        self._selection_model = self.blueprintModel.buildStepSelectionModel

        self.ui = Ui_ActionTree()
        self.ui.setupUi(self)

        # add action tree view
        self.action_tree_view = ActionTreeView(self.blueprintModel, self)
        self.action_tree_view.setModel(self.model)
        self.action_tree_view.setSelectionModel(self._selection_model)
        self.action_tree_view.expandAll()
        self.ui.main_layout.addWidget(self.action_tree_view)

        # connect signals
        self.model.modelReset.connect(self._on_model_reset)
        self.blueprintModel.changeSceneFinished.connect(self._onChangeSceneFinished)
        self.blueprintModel.fileChanged.connect(self._onFileChanged)

        self._onFileChanged()

    def _onChangeSceneFinished(self):
        self._onFileChanged()

    def _onFileChanged(self):
        # don't update until after scene change is finished
        if self.blueprintModel.isChangingScenes:
            return

        if self.blueprintModel.isFileOpen():
            self.ui.main_stack.setCurrentWidget(self.ui.active_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.inactive_page)

    def _on_model_reset(self):
        self.action_tree_view.expandAll()

    def setupActionsMenu(self, parent: Optional[QtCore.QObject], menu_bar: QtWidgets.QMenuBar):
        """
        Set up the Actions menu on a menu bar.
        """
        actions_menu = menu_bar.addMenu("Actions")

        add_defaults_action = QtWidgets.QAction("Add Default Actions", parent)
        add_defaults_action.setStatusTip("Add the default set of actions.")
        add_defaults_action.triggered.connect(self.blueprintModel.addDefaultActions)
        actions_menu.addAction(add_defaults_action)

        actions_menu.addSeparator()

        allActionSpecs: List[BuildActionSpec] = BuildActionRegistry.get().get_all_actions()

        grp_action = QtWidgets.QAction("Group", parent)
        grp_action.triggered.connect(self.blueprintModel.createGroup)
        actions_menu.addAction(grp_action)

        # create action sub menu for each category
        categories = [spec.category for spec in allActionSpecs]
        categories = list(set(categories))
        cat_menus: Dict[str, QtWidgets.QMenu] = {}

        for cat in sorted(categories):
            cat_menu = actions_menu.addMenu(cat)
            cat_menus[cat] = cat_menu

        for actionSpec in allActionSpecs:
            actionId = actionSpec.id
            actionCategory = actionSpec.category
            description = actionSpec.description

            action = QtWidgets.QAction(actionSpec.display_name, parent)
            if description:
                action.setStatusTip(description)
            action.triggered.connect(partial(self.blueprintModel.createAction, actionId))

            cat_menus[actionCategory].addAction(action)


class ActionTreeWindow(PulseWindow):
    """
    A standalone window that contains an Action Tree.
    """

    OBJECT_NAME = "pulseActionTreeWindow"
    WINDOW_MODULE = "pulse.ui.actiontree"
    WINDOW_TITLE = "Pulse Action Tree"
    WIDGET_CLASS = ActionTree

    def __init__(self, parent=None):
        super(ActionTreeWindow, self).__init__(parent)

        # setup main menu bar
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.layout().setMenuBar(self.menu_bar)

        self.main_widget.setupActionsMenu(self, self.menu_bar)
