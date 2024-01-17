"""
Tree widget for displaying the build step hierarchy of a blueprint.
"""
from __future__ import annotations

import logging
from functools import partial
from typing import Optional, cast

import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets, QtGui

from .core import BlueprintUIModel, BuildStepTreeModel
from .core import PulseWindow
from .gen.action_tree import Ui_ActionTree
from ..core import BuildStep, BuildActionRegistry, BuildActionSpec

LOG = logging.getLogger(__name__)


class ActionTreeStyledItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ActionTreeStyledItemDelegate, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.get_default_model()

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super(ActionTreeStyledItemDelegate, self).paint(painter, option, index)


class ActionTreeView(QtWidgets.QTreeView):
    """
    A tree view for displaying BuildActions in a Blueprint
    """

    def __init__(self, blueprint_model=None, parent=None):
        super().__init__(parent=parent)

        self.blueprint_model = blueprint_model

        self.setItemDelegate(ActionTreeStyledItemDelegate(parent))
        self.setHeaderHidden(True)
        self.setAcceptDrops(True)
        self.setRootIsDecorated(False)
        self.setExpandsOnDoubleClick(False)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setIndentation(14)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            self._delete_selected_items()
            return True

        elif key == QtCore.Qt.Key_D:
            self._toggle_selected_items_disabled()
            return True

        elif key == QtCore.Qt.Key_M:
            self._mirror_selected_items()
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

    def _delete_selected_items(self):
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps: list[BuildStep] = []
        for index in indexes:
            step: BuildStep = cast(BuildStepTreeModel, self.model()).step_for_index(index)
            if step and not step.is_root():
                steps.append(step)
        if not steps:
            return

        steps = BuildStep.get_topmost_steps(steps)
        paths = [step.get_full_path() for step in steps]

        LOG.info(f"Deleting {paths}")
        cmds.undoInfo(openChunk=True, chunkName="Delete Pulse Actions")
        for path in paths:
            cmds.pulseDeleteStep(path)
        cmds.undoInfo(closeChunk=True)

    def _toggle_selected_items_disabled(self):
        """
        Toggle the disabled state of the selected items.
        If item disable states are mismatched, will disable all items.
        """
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps = []
        for index in indexes:
            step = cast(BuildStepTreeModel, self.model()).step_for_index(index)
            if step:
                steps.append((index, step))

        # only include steps with parents to ignore the root step, which can't be disabled
        all_disabled = all([s.is_disabled for i, s in steps if s.parent])
        new_disabled = False if all_disabled else True
        for index, step in steps:
            self.model().setData(index, new_disabled, QtCore.Qt.CheckStateRole)

    def _mirror_selected_items(self):
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps: list[BuildStep] = []
        for index in indexes:
            step: BuildStep = cast(BuildStepTreeModel, self.model()).step_for_index(index)
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
        self.blueprint_model = BlueprintUIModel.get_default_model()
        self.model = self.blueprint_model.build_step_tree_model
        self._selection_model = self.blueprint_model.build_step_selection_model

        self.ui = Ui_ActionTree()
        self.ui.setupUi(self)

        # add action tree view
        self.action_tree_view = ActionTreeView(self.blueprint_model, self)
        self.action_tree_view.setModel(self.model)
        self.action_tree_view.setSelectionModel(self._selection_model)
        self.action_tree_view.expandAll()
        self.ui.main_layout.addWidget(self.action_tree_view)

        # connect signals
        self.model.modelReset.connect(self._on_model_reset)
        self.blueprint_model.change_scene_finished.connect(self._on_change_scene_finished)
        self.blueprint_model.file_changed.connect(self._on_file_changed)

        self._on_file_changed()

    def _on_change_scene_finished(self):
        self._on_file_changed()

    def _on_file_changed(self):
        # don't update until after scene change is finished
        if self.blueprint_model.is_changing_scenes:
            return

        if self.blueprint_model.is_file_open():
            self.ui.main_stack.setCurrentWidget(self.ui.active_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.inactive_page)

    def _on_model_reset(self):
        self.action_tree_view.expandAll()

    def setup_actions_menu(self, parent: Optional[QtCore.QObject], menu_bar: QtWidgets.QMenuBar):
        """
        Set up the Actions menu on a menu bar.
        """
        actions_menu = menu_bar.addMenu("Actions")

        add_defaults_action = QtWidgets.QAction("Reset To Default", parent)
        add_defaults_action.setStatusTip("Reset the Blueprint to the default set of actions.")
        add_defaults_action.triggered.connect(self.blueprint_model.reset_to_default_with_prompt)
        actions_menu.addAction(add_defaults_action)

        actions_menu.addSeparator()

        all_action_specs: list[BuildActionSpec] = BuildActionRegistry.get().get_all_actions()

        grp_action = QtWidgets.QAction("Group", parent)
        grp_action.triggered.connect(self.blueprint_model.create_group)
        actions_menu.addAction(grp_action)

        # create action sub menu for each category
        categories = [spec.category for spec in all_action_specs]
        categories = list(set(categories))
        cat_menus: dict[str, QtWidgets.QMenu] = {}

        for cat in sorted(categories):
            cat_menu = actions_menu.addMenu(cat)
            cat_menus[cat] = cat_menu

        for actionSpec in all_action_specs:
            action_id = actionSpec.id
            action_category = actionSpec.category
            description = actionSpec.description

            action = QtWidgets.QAction(actionSpec.display_name, parent)
            if description:
                action.setStatusTip(description)
            action.triggered.connect(partial(self.blueprint_model.create_action, action_id))

            cat_menus[action_category].addAction(action)


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

        self.main_widget.setup_actions_menu(self, self.menu_bar)
