"""
UI model classes, and base classes for common widgets.
"""

from __future__ import annotations

import logging
import os
from typing import Optional, List, cast

import maya.OpenMaya as api
import maya.OpenMayaUI as mui
import maya.cmds as cmds
import pymel.core as pm
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from .utils import CollapsibleFrame
from .utils import dpi_scale
from .. import editor_utils
from ..core import Blueprint, BlueprintSettings, BlueprintBuilder, BlueprintValidator
from ..core import BuildStep, BuildAction
from ..core import get_all_rigs
from ..core import load_actions
from ..core import serialize_attr_value
from ..editor_utils import open_blueprint_scene
from ..prefs import option_var_property
from ..vendor import pymetanode as meta
from ..vendor.Qt import QtCore, QtWidgets, QtGui

LOG = logging.getLogger(__name__)
LOG.level = logging.DEBUG


class PulsePanelWidget(QtWidgets.QWidget):
    """
    A collapsible container widget with a title bar.
    """

    # TODO: move this class to a common widgets module, it's not core functionality

    def __init__(self, parent):
        super(PulsePanelWidget, self).__init__(parent=parent)

        # the main widget that will be shown and hidden when collapsing this container
        self._content_widget = None

        self.setup_ui(self)

    def set_title_text(self, text: str):
        """
        Set the title text for the panel.
        """
        self.title_label.setText(text)

    def setup_ui(self, parent):
        self.main_layout = QtWidgets.QVBoxLayout(parent)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(3)

        # header frame
        self.header_frame = CollapsibleFrame(parent)
        self.header_frame.collapsedChanged.connect(self._on_collapsed_changed)

        # header layout
        self.header_layout = QtWidgets.QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(0, 0, 0, 0)

        # title label
        self.title_label = QtWidgets.QLabel(self.header_frame)
        self.title_label.setProperty("cssClasses", "section-title")
        self.header_layout.addWidget(self.title_label)

        self.main_layout.addWidget(self.header_frame)

    def set_content_widget(self, widget: QtWidgets.QWidget):
        """
        Set the widget to use for the contents of the panel.
        """
        self._content_widget = widget
        if self._content_widget:
            self._content_widget.setVisible(not self.header_frame.is_collapsed())
            self.main_layout.addWidget(self._content_widget)

    def _on_collapsed_changed(self, is_collapsed):
        if self._content_widget:
            self._content_widget.setVisible(not is_collapsed)


class PulseWindow(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """
    A base class for any standalone window in the Pulse UI. Integrates
    the Maya builtin dockable mixin, and prevents multiple instances
    of the window.
    """

    OBJECT_NAME = None

    # the display title of the window
    WINDOW_TITLE = None

    # window size hints, set to a QtCore.QSize to override, otherwise define in the .ui
    PREFERRED_SIZE = None
    STARTING_SIZE = None
    MINIMUM_SIZE = None

    # the name of the module in which this window class can be found,
    # used to build the UI_SCRIPT and CLOSE_SCRIPT that Maya uses to restore windows on startup
    WINDOW_MODULE = None

    # default area where this window should be docked, note that the 'areas' are large
    # sections at the extremes of the maya window, and DEFAULT_TAB_CONTROL should be used
    # when attempting to dock to smaller areas like the Channel Box
    DEFAULT_DOCK_AREA = None

    # if set, dock this window as a tab into the specified control
    # options include "ChannelBoxLayerEditor", "AttributeEditor", "Outliner"
    DEFAULT_TAB_CONTROL = None

    # a string of python code to run when the workspace control is shown
    UI_SCRIPT = "from {module} import {cls}\n{cls}.createWindow(restore=True)"

    # a string of python code to run when the workspace control is closed
    CLOSE_SCRIPT = "from {module} import {cls}\n{cls}.windowClosed()"

    REQUIRED_PLUGINS = ["pulse"]

    # reference to singleton instance
    INSTANCE = None

    # the file path to the stylesheet for this window, relative to this module
    STYLESHEET_PATH = "style/window_style.qss"

    # if set, instantiate a single QWidget of this class and wrap it in a simple layout
    WIDGET_CLASS = None

    @classmethod
    def createWindow(cls, restore=False):
        if restore:
            parent = mui.MQtUtil.getCurrentParent()

        # create instance if it doesn't exist
        if not cls.INSTANCE:
            # load required plugins
            if cls.REQUIRED_PLUGINS:
                for plugin in cls.REQUIRED_PLUGINS:
                    pm.loadPlugin(plugin, quiet=True)

            cls.INSTANCE = cls()

        if restore:
            mixin_ptr = mui.MQtUtil.findControl(cls.INSTANCE.objectName())
            mui.MQtUtil.addWidgetToMayaLayout(int(mixin_ptr), int(parent))
        else:
            ui_script = cls.UI_SCRIPT.format(module=cls.WINDOW_MODULE, cls=cls.__name__)
            close_script = cls.CLOSE_SCRIPT.format(module=cls.WINDOW_MODULE, cls=cls.__name__)

            cls.INSTANCE.show(
                dockable=True,
                floating=(cls.DEFAULT_DOCK_AREA is None),
                area=cls.DEFAULT_DOCK_AREA,
                uiScript=ui_script,
                closeCallback=close_script,
                requiredPlugin=cls.REQUIRED_PLUGINS,
            )

            # if set, dock the control as a tab of an existing control
            if cls.DEFAULT_TAB_CONTROL:
                cmds.workspaceControl(cls.getWorkspaceControlName(), e=True, tabToControl=[cls.DEFAULT_TAB_CONTROL, -1])

        return cls.INSTANCE

    @classmethod
    def getWorkspaceControlName(cls):
        return cls.OBJECT_NAME + "WorkspaceControl"

    @classmethod
    def destroyWindow(cls):
        if cls.windowExists():
            cls.hideWindow()
            cmds.deleteUI(cls.getWorkspaceControlName(), control=True)

    @classmethod
    def showWindow(cls):
        if cls.windowExists():
            cmds.workspaceControl(cls.getWorkspaceControlName(), e=True, restore=True)
        else:
            cls.createWindow()

    @classmethod
    def hideWindow(cls):
        """
        Close the window, if it exists
        """
        if cls.windowExists():
            cmds.workspaceControl(cls.getWorkspaceControlName(), e=True, vis=False)

    @classmethod
    def toggleWindow(cls):
        if cls.isRaised():
            cls.destroyWindow()
        else:
            cls.showWindow()

    @classmethod
    def windowClosed(cls):
        cls.INSTANCE = None

    @classmethod
    def windowExists(cls):
        """
        Return True if an instance of this window exists
        """
        return cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True)

    @classmethod
    def isRaised(cls):
        """
        Return True if the window is visible and raised on screen.
        False when collapsed, hidden, or not the active tab in a tab group.
        """
        return cls.windowExists() and cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, r=True)

    def __init__(self, parent=None):
        super(PulseWindow, self).__init__(parent=parent)

        self.setObjectName(self.OBJECT_NAME)

        if self.WINDOW_TITLE:
            self.setWindowTitle(self.WINDOW_TITLE)

        self.preferredSize = self.PREFERRED_SIZE

        if self.STARTING_SIZE:
            self.resize(dpi_scale(self.STARTING_SIZE))

        self._apply_stylesheet()

        self.main_widget = None
        if self.WIDGET_CLASS:
            self._setup_widget_ui(self.WIDGET_CLASS)

    def setSizeHint(self, size):
        self.preferredSize = size

    def sizeHint(self):
        if self.preferredSize:
            return self.preferredSize
        return super().sizeHint()

    def minimumSizeHint(self):
        if self.MINIMUM_SIZE:
            return self.MINIMUM_SIZE
        return super().minimumSizeHint()

    def _apply_stylesheet(self):
        if self.STYLESHEET_PATH:
            # combine style sheet path with this module's directory
            module_dir = os.path.dirname(__file__)
            full_path = os.path.join(module_dir, self.STYLESHEET_PATH)

            if os.path.isfile(full_path):
                # found the stylesheet, apply it
                with open(full_path, "r") as fp:
                    self.setStyleSheet(fp.read())
            else:
                LOG.warning(f"Could not find stylesheet: {full_path}")

    def _setup_widget_ui(self, widget_cls):
        """
        Set up a basic layout with no margin and a single widget.

        Args:
            widget_cls: class
                The QWidget class to instantiate and wrap in a simple layout.
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.main_widget = widget_cls(self)
        layout.addWidget(self.main_widget)


class BlueprintUIModel(QtCore.QObject):
    """
    The owner and manager of various models representing a Blueprint in the scene.
    All reading and writing for the Blueprint through the UI should be done using this model.

    Blueprints represented in this model are saved and loaded using yaml
    files which are paired with a maya scene file.
    """

    # shared instance
    _instance: BlueprintUIModel | None = None

    # automatically save the blueprint file when the maya scene is saved
    auto_save = option_var_property("pulse.editor.auto_save", True)

    # automatically load the blueprint file when a maya scene is opened
    auto_load = option_var_property("pulse.editor.auto_load", True)

    # automatically show the action editor when selecting an action in the tree
    auto_show_action_editor = option_var_property("pulse.editor.auto_show_action_editor", True)

    # automatically save the maya scene before building
    auto_save_scene_on_build = option_var_property("pulse.editor.auto_save_scene_on_build", True)

    # automatically save the blueprint before building
    auto_save_blueprint_on_build = option_var_property("pulse.editor.auto_save_blueprint_on_build", True)

    def set_auto_save(self, value):
        self.auto_save = value

    def set_auto_load(self, value):
        self.auto_load = value

    def set_auto_show_action_editor(self, value):
        self.auto_show_action_editor = value

    def set_auto_save_scene_on_build(self, value):
        self.auto_save_scene_on_build = value

    def set_auto_save_blueprint_on_build(self, value):
        self.auto_save_blueprint_on_build = value

    # called after a scene change (new or opened) to allow ui to update
    # if it was previously frozen while is_changing_scenes is true
    change_scene_finished = QtCore.Signal()

    # called when the current blueprint file has changed
    file_changed = QtCore.Signal()

    # called when the modified status of the file has changed
    is_file_modified_changed = QtCore.Signal(bool)

    # called when the read-only state of the blueprint has changed
    read_only_changed = QtCore.Signal(bool)

    # called when a Blueprint setting has changed, passes the setting key and new value
    setting_changed = QtCore.Signal(str, object)

    # called when the presence of a built rig has changed
    rig_exists_changed = QtCore.Signal()

    # called when validation results have changed
    on_validate_event = QtCore.Signal()

    @classmethod
    def get(cls) -> BlueprintUIModel:
        """
        Return the shared model instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def delete(cls):
        """
        Delete the shared model.
        """
        if cls._instance:
            cls._instance.on_delete()
            cls._instance = None

    @classmethod
    def get_default_model(cls) -> BlueprintUIModel:
        """
        Deprecated: Use BlueprintUIModel.get() instead.
        """
        return cls.get()

    def __init__(self, parent=None):
        super(BlueprintUIModel, self).__init__(parent=parent)

        # load actions if they haven't been already
        load_actions()

        # the current Blueprint asset
        self._blueprint: Blueprint | None = None

        # the tree item model and selection model for BuildSteps
        self.build_step_tree_model = BuildStepTreeModel(self.blueprint, self, self)
        self.build_step_selection_model = BuildStepSelectionModel(self.build_step_tree_model, self)

        # the interactive builder that is currently running, if any
        self.interactive_builder: Optional[BlueprintBuilder] = None

        # register maya scene callbacks that can be used for auto save and load
        self.is_changing_scenes = False
        self._callback_ids = []
        self._add_scene_callbacks()

        # keep track of whether a rig is currently in the scene to determine which mode we are in
        self.does_rig_exist = False
        self._refresh_rig_exists()

        if self.auto_load:
            self.try_open_file(self.get_blueprint_file_path_for_scene())

    def on_delete(self):
        self._remove_scene_callbacks()

    @property
    def blueprint(self) -> Blueprint | None:
        return self._blueprint

    def set_blueprint(self, blueprint: Blueprint | None):
        """
        Set the current Blueprint asset
        """
        self.build_step_tree_model.beginResetModel()
        self._blueprint = blueprint
        self.build_step_tree_model.endResetModel()
        self.is_file_modified_changed.emit(self.is_file_modified())
        self.file_changed.emit()
        self.read_only_changed.emit(self.is_read_only())

    def is_file_open(self) -> bool:
        """
        Is a Blueprint File currently available?
        """
        return self.blueprint is not None

    def is_file_modified(self) -> bool:
        """
        Return whether modifications have been made to the open Blueprint File since it was last saved.
        """
        return self.is_file_open() and self.blueprint.is_modified()

    def modify(self):
        """
        Mark the current blueprint file as modified.
        """
        if self.is_file_open() and not self.is_read_only():
            self.blueprint.modify()
            self.is_file_modified_changed.emit(self.is_file_modified())

    def is_read_only(self) -> bool:
        """
        Return True if the modifications to the Blueprint are not allowed.
        """
        if self.does_rig_exist:
            # readonly whenever a rig is around
            return True

        if not self.is_file_open():
            # no blueprint open to edit
            return True

        return self.blueprint.is_read_only

    def get_blueprint_file_path(self) -> Optional[str]:
        """
        Return the full path of the current Blueprint File.
        """
        if self.is_file_open():
            return self.blueprint.file_path

    def get_blueprint_file_name(self) -> Optional[str]:
        """
        Return the base name of the current Blueprint File.
        """
        if self.is_file_open():
            return self.blueprint.get_file_name()

    def can_save(self) -> bool:
        """
        Can the blueprint file currently be saved?
        """
        self._refresh_rig_exists()
        return self.is_file_open() and self.blueprint.can_save() and not self.is_read_only()

    def can_load(self) -> bool:
        """
        Can the blueprint file currently be loaded?
        """
        return self.is_file_open() and self.blueprint.can_load()

    def new_file(self, use_default_actions=True):
        """
        Start a new Blueprint File.
        Does not write the file to disk.

        Args:
            use_default_actions (bool): If true, add the default build actions from blueprint config
        """
        # close first, prompting to save
        if self.is_file_open():
            if not self.close_file():
                return

        new_blueprint = Blueprint(file_path=self.get_new_blueprint_file_path())
        new_blueprint.set_setting(BlueprintSettings.RIG_NAME, "untitled")
        if use_default_actions:
            new_blueprint.reset_to_default()

        self.set_blueprint(new_blueprint)

    def get_new_blueprint_file_path(self) -> str | None:
        """
        Return the path to use for a new Blueprint.
        """
        file_path = self.get_blueprint_file_path_for_scene()
        # don't use an existing file
        if file_path and not os.path.isfile(file_path):
            return file_path

    def get_blueprint_file_path_for_scene(self) -> str | None:
        """
        Return the Blueprint file path to use for the current scene.
        """
        scene_name = pm.sceneName()
        if scene_name:
            base_name = os.path.splitext(scene_name)[0]
            return f"{base_name}.{Blueprint.file_ext}"

    def try_open_file(self, file_path: str | None, read_only=False):
        """
        Try to open a Blueprint asset, but only if it exists
        """
        if file_path and os.path.isfile(file_path):
            self.open_file(file_path, read_only)

    def open_file(self, file_path: str, read_only=False):
        """
        Open a Blueprint asset.

        Args:
            file_path: str
                The path to a blueprint.
            read_only: bool
                Open the asset as read-only.
        """
        # close first, prompting to save
        if self.is_file_open():
            if not self.close_file():
                return

        new_blueprint = Blueprint(file_path=file_path, is_read_only=read_only)
        new_blueprint.load()

        self.set_blueprint(new_blueprint)

        self.file_changed.emit()
        self.read_only_changed.emit(self.is_read_only())

    def open_file_with_prompt(self):
        # default to opening from the directory of the maya scene
        kwargs = {}
        scene_name = pm.sceneName()
        if scene_name:
            scene_dir = str(scene_name.parent)
            kwargs["startingDirectory"] = scene_dir

        file_path_results = pm.fileDialog2(fileMode=1, fileFilter="Pulse Blueprint(*.yml)", **kwargs)
        if file_path_results:
            file_path = file_path_results[0]
            self.open_file(file_path)

    def save_file(self) -> bool:
        """
        Save the current Blueprint File.

        Returns:
            True if the file was saved.
        """
        if self.can_save():
            success = self.blueprint.save()
            self.is_file_modified_changed.emit(self.is_file_modified())
            return success
        return False

    def save_file_as(self, file_path: str) -> bool:
        """
        Save the current Blueprint File to a different file path.

        Returns:
            True if the file was saved.
        """
        if not self.is_file_open():
            return False

        success = self.blueprint.save_as(file_path)
        self.file_changed.emit()
        self.is_file_modified_changed.emit(self.is_file_modified())
        return success

    def _save_file_with_prompt(self, force_prompt=False) -> bool:
        if not self.is_file_open():
            LOG.error("Nothing to save.")
            return False

        if self.is_read_only():
            LOG.error("Cannot save read-only Blueprint")
            return False

        if force_prompt or not self.blueprint.has_file_path():
            # prompt for file path
            file_path_results = pm.fileDialog2(cap="Save Blueprint", fileFilter="Pulse Blueprint (*.yml)")
            if not file_path_results:
                return False
            self.blueprint.file_path = file_path_results[0]
            self.file_changed.emit()

        self.save_file()
        return True

    def save_file_with_prompt(self) -> bool:
        """
        Save the current Blueprint file, prompting for a file path if none is set.

        Returns:
            True if the file was saved.
        """
        return self._save_file_with_prompt()

    def save_file_as_with_prompt(self) -> bool:
        """
        Save the current Blueprint file to a new path, prompting for the file path.

        Returns:
            True if the file was saved.
        """
        return self._save_file_with_prompt(force_prompt=True)

    def save_or_discard_changes_with_prompt(self) -> bool:
        """
        Save or discard modifications to the current Blueprint File.

        Returns:
            True if the user chose to Save or Not Save, False if they chose to Cancel.
        """
        file_path = self.get_blueprint_file_path()
        if file_path:
            message = f"Save changes to {file_path}?"
        else:
            message = f"Save changes to unsaved Blueprint?"
        response = pm.confirmDialog(
            title="Save Blueprint Changes",
            message=message,
            button=["Save", "Don't Save", "Cancel"],
            dismissString="Cancel",
        )
        if response == "Save":
            return self.save_file_with_prompt()
        elif response == "Don't Save":
            return True
        else:
            return False

    def reload_file(self):
        """
        Reload the current Blueprint asset from disk.
        """
        if not self.can_load():
            return

        if self.is_file_modified():
            # confirm loss of changes
            file_path = self.get_blueprint_file_path()
            response = pm.confirmDialog(
                title="Reload Blueprint",
                message=f"Are you sure you want to reload {file_path}? " "All changes will be lost.",
                button=["Reload", "Cancel"],
                dismissString="Cancel",
            )
            if response != "Reload":
                return

        new_blueprint = Blueprint(file_path=self.blueprint.file_path)
        new_blueprint.load()
        self.set_blueprint(new_blueprint)

    def close_file(self, prompt_save_changes=True) -> bool:
        """
        Close the current Blueprint File.
        Returns true if the file was successfully closed, or false if canceled due to unsaved changes.
        """
        if prompt_save_changes and self.is_file_modified():
            if not self.save_or_discard_changes_with_prompt():
                return False

        self.set_blueprint(None)
        return True

    def get_setting(self, key, default=None):
        """
        Helper to return a Blueprint setting.
        """
        if self.is_file_open():
            return self.blueprint.get_setting(key, default)
        return default

    def set_setting(self, key, value):
        """
        Set a Blueprint setting.
        """
        if not self.is_file_open():
            return

        if self.is_read_only():
            LOG.error("set_setting: Cannot edit readonly Blueprint")
            return

        old_value = self.blueprint.get_setting(key)
        if old_value != value:
            self.blueprint.set_setting(key, value)
            self.modify()
            self.setting_changed.emit(key, value)

    def _refresh_rig_exists(self):
        old_read_only = self.is_read_only()
        self.does_rig_exist = len(get_all_rigs()) > 0
        self.rig_exists_changed.emit()

        if old_read_only != self.is_read_only():
            self.read_only_changed.emit(self.is_read_only())

    def _add_scene_callbacks(self):
        if not self._callback_ids:
            save_id = api.MSceneMessage.addCallback(api.MSceneMessage.kBeforeSave, self._on_before_save_scene)
            self._callback_ids.append(save_id)
            before_open_id = api.MSceneMessage.addCallback(api.MSceneMessage.kBeforeOpen, self._on_before_open_scene)
            self._callback_ids.append(before_open_id)
            after_open_id = api.MSceneMessage.addCallback(api.MSceneMessage.kAfterOpen, self._on_after_open_scene)
            self._callback_ids.append(after_open_id)
            before_new_id = api.MSceneMessage.addCallback(api.MSceneMessage.kBeforeNew, self._on_before_new_scene)
            self._callback_ids.append(before_new_id)
            after_new_id = api.MSceneMessage.addCallback(api.MSceneMessage.kAfterNew, self._on_after_new_scene)
            self._callback_ids.append(after_new_id)

    def _remove_scene_callbacks(self):
        if self._callback_ids:
            while self._callback_ids:
                callback_id = self._callback_ids.pop()
                api.MMessage.removeCallback(callback_id)

    def _on_before_save_scene(self, client_data=None):
        if self._should_auto_save():
            LOG.debug("Auto-saving Blueprint...")
            self.save_file_with_prompt()

    def _on_before_open_scene(self, client_data=None):
        self.is_changing_scenes = True
        self.close_file()

    def _on_after_open_scene(self, client_data=None):
        self.is_changing_scenes = False
        self._refresh_rig_exists()
        if self.auto_load:
            self.try_open_file(self.get_blueprint_file_path_for_scene())
        self.change_scene_finished.emit()

    def _on_before_new_scene(self, client_data=None):
        self.is_changing_scenes = True
        self.close_file()

    def _on_after_new_scene(self, client_data=None):
        self.is_changing_scenes = False
        self._refresh_rig_exists()
        self.change_scene_finished.emit()

    def _should_auto_save(self):
        return self.auto_save and self.is_file_open()

    def reset_to_default_with_prompt(self):
        """
        Reset the Blueprint to the default set of actions.
        """
        if self.is_file_open() and not self.is_read_only():
            response = pm.confirmDialog(
                title="Reset Blueprint",
                message="Are you sure you want to reset the Blueprint? This action is not undoable.",
                button=["Reset", "Cancel"],
                defaultButton="Cancel",
                dismissString="Cancel",
                cancelButton="Cancel",
            )

            if response != "Reset":
                return

            self.build_step_tree_model.beginResetModel()
            self.blueprint.reset_to_default()
            self.build_step_tree_model.endResetModel()
            self.modify()

    def create_step(self, parent_path, child_index, data) -> Optional[BuildStep]:
        """
        Create a new BuildStep

        Args:
            parent_path (str): The path to the parent step
            child_index (int): The index at which to insert the new step
            data (dict): The serialized data for the BuildStep to create

        Returns:
            The newly created BuildStep, or None if the operation failed.
        """
        if self.is_read_only():
            LOG.error("create_step: Cannot edit readonly Blueprint")
            return

        parent_step = self.blueprint.get_step_by_path(parent_path)
        if not parent_step:
            LOG.error("create_step: failed to find parent step: %s", parent_path)
            return

        parent_index = self.build_step_tree_model.index_by_step(parent_step)
        self.build_step_tree_model.beginInsertRows(parent_index, child_index, child_index)

        try:
            step = BuildStep.from_data(data)
        except ValueError as e:
            LOG.error("Failed to create build step: %s" % e, exc_info=True)
            return

        parent_step.insert_child(child_index, step)

        self.build_step_tree_model.endInsertRows()
        self.modify()
        return step

    def delete_step(self, step_path):
        """
        Delete a BuildStep

        Returns:
            True if the step was deleted successfully
        """
        if self.is_read_only():
            LOG.error("delete_step: Cannot edit readonly Blueprint")
            return False

        step = self.blueprint.get_step_by_path(step_path)
        if not step:
            LOG.error("delete_step: failed to find step: %s", step_path)
            return False

        step_index = self.build_step_tree_model.index_by_step(step)
        self.build_step_tree_model.beginRemoveRows(step_index.parent(), step_index.row(), step_index.row())

        step.remove_from_parent()

        self.build_step_tree_model.endRemoveRows()
        self.modify()
        return True

    def move_step(self, source_path, target_path):
        """
        Move a BuildStep from source path to target path.

        Returns:
            The new path (str) of the build step, or None if
            the operation failed.
        """
        if self.is_read_only():
            LOG.error("move_step: Cannot edit readonly Blueprint")
            return

        step = self.blueprint.get_step_by_path(source_path)
        if not step:
            LOG.error("move_step: failed to find step: %s", source_path)
            return

        if step.is_root():
            LOG.error("move_step: cannot move root step")
            return

        self.build_step_tree_model.layoutAboutToBeChanged.emit()

        source_parent_path = os.path.dirname(source_path)
        target_parent_path = os.path.dirname(target_path)
        if source_parent_path != target_parent_path:
            step.set_parent(self.blueprint.get_step_by_path(target_parent_path))
        target_name = os.path.basename(target_path)
        step.set_name(target_name)

        self.build_step_tree_model.layoutChanged.emit()
        self.modify()
        return step.get_full_path()

    def rename_step(self, step_path, target_name):
        if self.is_read_only():
            LOG.error("rename_step: Cannot edit readonly Blueprint")
            return

        step = self.blueprint.get_step_by_path(step_path)
        if not step:
            LOG.error("move_step: failed to find step: %s", step_path)
            return

        if step.is_root():
            LOG.error("move_step: cannot rename root step")
            return

        old_name = step.name
        step.set_name(target_name)

        if step.name != old_name:
            self._emit_step_changed(step)

        return step.get_full_path()

    def create_steps_for_selection(self, step_data: Optional[str] = None):
        """
        Create new BuildSteps in the hierarchy at the current selection and return the new step paths.

        Args:
            step_data: str
                A string representation of serialized BuildStep data used to create the new steps.
        """
        if self.is_read_only():
            LOG.warning("cannot create steps, blueprint is read only")
            return

        LOG.debug("creating new steps at selection: %s", step_data)

        sel_indexes = self.build_step_selection_model.selectedIndexes()
        if not sel_indexes:
            sel_indexes = [QtCore.QModelIndex()]

        model: BuildStepTreeModel = self.build_step_selection_model.model()

        def _get_parent_and_insert_index(_index) -> tuple[BuildStep, int]:
            step = model.step_for_index(_index)
            LOG.debug("step: %s", step)
            if step.can_have_children():
                LOG.debug("inserting at num children: %d", step.num_children())
                return step, step.num_children()
            else:
                LOG.debug("inserting at selected + 1: %d", _index.row() + 1)
                return step.parent, _index.row() + 1

        new_paths = []
        for index in sel_indexes:
            parent_step, insert_index = _get_parent_and_insert_index(index)
            parent_path = parent_step.get_full_path() if parent_step else None
            if not parent_path:
                parent_path = ""
            if not step_data:
                step_data = ""
            new_step_path = cmds.pulseCreateStep(parent_path, insert_index, step_data)
            if new_step_path:
                # TODO: remove this if/when plugin command only returns single string
                new_step_path = new_step_path[0]
                new_paths.append(new_step_path)
            # if self.model.insertRows(insertIndex, 1, parent_index):
            #     newIndex = self.model.index(insertIndex, 0, parent_index)
            #     newPaths.append(newIndex)

        self.modify()
        return new_paths

    def create_group(self):
        if self.is_read_only():
            LOG.warning("Cannot create group, blueprint is read-only")
            return

        LOG.debug("create_group")
        new_paths = self.create_steps_for_selection()
        self.build_step_selection_model.set_selected_item_paths(new_paths)

    def create_action(self, action_id: str):
        if self.is_read_only():
            LOG.warning("Cannot create action, blueprint is read-only")
            return

        LOG.debug("create_action: %s", action_id)
        step_data = "{'action':{'id':'%s'}}" % action_id
        new_paths = self.create_steps_for_selection(step_data=step_data)
        self.build_step_selection_model.set_selected_item_paths(new_paths)

    def get_step(self, step_path: str) -> BuildStep:
        """
        Return the BuildStep at a path
        """
        return self.blueprint.get_step_by_path(step_path)

    def get_step_data(self, step_path: str):
        """
        Return the serialized data for a step at a path
        """
        step = self.get_step(step_path)
        if step:
            return step.serialize()

    def get_action_data(self, step_path: str):
        """
        Return serialized data for a BuildActionProxy
        """
        step = self.get_step(step_path)
        if not step:
            return

        if not step.is_action():
            LOG.error("get_action_data: %s step is not an action", step)
            return

        return step.action_proxy.serialize()

    def set_action_data(self, step_path, data):
        """
        Replace all attribute values on a BuildActionProxy.
        """
        step = self.get_step(step_path)
        if not step:
            return

        if not step.is_action():
            LOG.error("set_action_data: %s step is not an action", step)
            return

        step.action_proxy.deserialize(data)

        self._emit_step_changed(step)

    def get_action_attr(self, attr_path, variant_index=-1):
        """
        Return the value of an attribute of a BuildAction

        Args:
            attr_path (str): The full path to an action attribute, e.g. 'My/Action.myAttr'
            variant_index (int): The index of the variant to retrieve, if the action has variants

        Returns:
            The attribute value, of varying types
        """
        step_path, attr_name = attr_path.split(".")

        step = self.get_step(step_path)
        if not step:
            return

        if not step.is_action():
            LOG.error("get_action_attr: %s is not an action", step)
            return

        if variant_index >= 0:
            if step.action_proxy.num_variants() > variant_index:
                variant = step.action_proxy.get_variant(variant_index)
                variant_attr = variant.get_attr(attr_name)
                if variant_attr:
                    return variant_attr.get_value()
        else:
            attr = step.action_proxy.get_attr(attr_name)
            if attr:
                return attr.get_value()

    def set_action_attr(self, attr_path, value, variant_index=-1):
        """
        Set the value for an attribute on the Blueprint
        """
        if self.is_read_only():
            LOG.error("set_action_attr: Cannot edit readonly Blueprint")
            return

        step_path, attr_name = attr_path.split(".")

        step = self.get_step(step_path)
        if not step:
            return

        if not step.is_action():
            LOG.error("set_action_attr: %s is not an action", step)
            return

        # TODO: log errors for missing attributes

        if variant_index >= 0:
            variant = step.action_proxy.get_or_create_variant(variant_index)
            variant_attr = variant.get_attr(attr_name)
            if variant_attr:
                variant_attr.set_value(value)
        else:
            attr = step.action_proxy.get_attr(attr_name)
            if attr:
                attr.set_value(value)

        self._emit_step_changed(step)

    def is_action_attr_variant(self, attr_path):
        step_path, attr_name = attr_path.split(".")

        step = self.get_step(step_path)
        if not step.is_action():
            LOG.error("is_action_attr_variant: {0} is not an action".format(step))
            return

        return step.action_proxy.is_variant_attr(attr_name)

    def set_is_action_attr_variant(self, attr_path, is_variant):
        """ """
        if self.is_read_only():
            LOG.error("set_is_action_attr_variant: Cannot edit readonly Blueprint")
            return

        step_path, attr_name = attr_path.split(".")

        step = self.get_step(step_path)
        if not step:
            return

        if not step.is_action():
            LOG.error("set_is_action_attr_variant: %s is not an action", step)
            return

        if is_variant:
            step.action_proxy.add_variant_attr(attr_name)
        else:
            step.action_proxy.remove_variant_attr(attr_name)

        self._emit_step_changed(step)

    def is_action_mirrored(self, step_path) -> bool:
        """Return whether a build action is mirrored."""
        step = self.get_step(step_path)
        if not step:
            return False

        if not step.is_action():
            LOG.error("set_is_action_mirrored: %s is not an action", step)
            return False

        return step.action_proxy.is_mirrored

    def set_is_action_mirrored(self, step_path, is_mirrored):
        """Set whether a build action is mirrored."""
        if self.is_read_only():
            LOG.error("set_is_action_mirrored: Cannot edit readonly Blueprint")
            return

        step = self.get_step(step_path)
        if not step:
            return

        if not step.is_action():
            LOG.error("set_is_action_mirrored: %s is not an action", step)
            return

        step.action_proxy.is_mirrored = is_mirrored

        self._emit_step_changed(step)

    def _emit_step_changed(self, step: BuildStep):
        index = self.build_step_tree_model.index_by_step(step)
        self.build_step_tree_model.dataChanged.emit(index, index, [])
        self.modify()

    def run_validation(self):
        """Run a Blueprint Validator for the current blueprint."""
        if not self.is_file_open():
            return

        if not BlueprintBuilder.pre_build_validate(self.blueprint):
            return

        validator = BlueprintValidator(self.blueprint)
        validator.start()

        self.on_validate_event.emit()

    def can_build(self) -> bool:
        return self.is_file_open() and not self.does_rig_exist

    def run_pre_build(self) -> bool:
        """
        Handle pre-build auto-saves, run build validation, and update the blueprint scene path.
        """
        if not BlueprintBuilder.pre_build_validate(self.blueprint):
            return False

        # save maya scene
        if self.auto_save_scene_on_build:
            if not editor_utils.save_scene_if_dirty(prompt=False):
                return False

        # update scene path, so we can re-open the current maya scene later
        self.blueprint.set_scene_path_to_current()

        # save blueprint
        if self.auto_save_blueprint_on_build:
            if self.is_file_modified():
                if not self.save_file_with_prompt():
                    return False

        return True

    def run_build(self):
        """Build the current blueprint."""
        if not self.can_build() or self.is_interactive_building():
            return False

        if not self.run_pre_build():
            return

        builder = BlueprintBuilder(self.blueprint)
        builder.start()

        # TODO: add build events so this can be done by observer pattern
        cmds.evalDeferred(self._refresh_rig_exists, low=True)

    def can_interactive_build(self) -> bool:
        return self.can_build()

    def is_interactive_building(self) -> bool:
        """Return true if an interactive build is currently active."""
        return self.interactive_builder is not None

    def run_interactive_build(self):
        if self.is_interactive_building() or not self.can_interactive_build():
            # already running
            return

        if not self.run_pre_build():
            return

        self.interactive_builder = BlueprintBuilder(self.blueprint)
        self.interactive_builder.cancel_on_interrupt = False
        self.interactive_builder.start(run=False)

        # auto run setup phase
        while True:
            self.interactive_builder.next()
            if self.interactive_builder.phase == "actions":
                break

        # TODO: add build event to refresh ui
        cmds.evalDeferred(self._refresh_rig_exists, low=True)

    def interactive_build_next_action(self):
        """Perform the next build action of an interactive build."""
        if self.interactive_builder:
            self.interactive_builder.next()
            if self.interactive_builder.is_finished:
                self.interactive_builder = None
            # TODO: add build event to refresh ui
            cmds.evalDeferred(self._refresh_rig_exists, low=True)

    def interactive_build_next_step(self):
        """Skip to the next build step of an interactive build."""
        if self.interactive_builder:
            step = self.interactive_builder.current_build_step_path
            while step == self.interactive_builder.current_build_step_path:
                self.interactive_builder.next()
                if self.interactive_builder.is_finished:
                    self.interactive_builder = None
                    break
                # TODO: add build event to refresh ui
                cmds.evalDeferred(self._refresh_rig_exists, low=True)

    def continue_interactive_build(self):
        """Resume running the current interactive build."""
        if self.interactive_builder:
            self.interactive_builder.run()
            if self.interactive_builder.is_finished:
                self.interactive_builder = None

    def cancel_interactive_build(self):
        if self.interactive_builder:
            self.interactive_builder.cancel()
            self.interactive_builder = None

    def open_blueprint_scene(self):
        """Open the blueprint maya scene for the first rig in the scene."""
        # TODO: don't need this stub, just listen for pre-close maya scene callback to clear interactive build
        self.cancel_interactive_build()
        open_blueprint_scene()


class BuildStepTreeModel(QtCore.QAbstractItemModel):
    """
    A Qt tree model for viewing and modifying the BuildStep hierarchy of a Blueprint.
    """

    def __init__(self, blueprint: Blueprint = None, blueprint_model: BlueprintUIModel = None, parent=None):
        super(BuildStepTreeModel, self).__init__(parent=parent)

        self.blueprint_model = blueprint_model

        # used to keep track of drag move actions since we don't have enough data
        # within one function to group undo chunks completely
        self._is_move_action_open = False

        # hacky, but used to rename dragged steps back to their original names since they will get
        # new names due to conflicts from both source and target steps existing at the same time briefly
        self._drag_rename_queue = []

    @property
    def blueprint(self) -> Blueprint:
        return self.blueprint_model.blueprint

    def is_read_only(self) -> bool:
        if self.blueprint_model:
            return self.blueprint_model.is_read_only()
        return False

    def step_for_index(self, index: QtCore.QModelIndex) -> Optional[BuildStep]:
        """
        Return the BuildStep of a QModelIndex.
        """
        if index.isValid():
            return cast(BuildStep, index.internalPointer())

    def index_by_step(self, step: BuildStep) -> QtCore.QModelIndex:
        if step:
            index_in_parent = step.index_in_parent()
            if index_in_parent >= 0:
                return self.createIndex(index_in_parent, 0, step)
        return QtCore.QModelIndex()

    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        """
        Create a QModelIndex for a row, column, and parent index
        """
        if not self.blueprint:
            # no data available
            return QtCore.QModelIndex()

        if column != 0:
            return QtCore.QModelIndex()

        if parent.isValid():
            parent_step = self.step_for_index(parent)
            if parent_step and parent_step.can_have_children():
                child_step = parent_step.get_child_at(row)
                if child_step:
                    return self.createIndex(row, column, child_step)
        elif row == 0:
            return self.createIndex(row, column, self.blueprint.root_step)

        return QtCore.QModelIndex()

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()

        child_step = self.step_for_index(index)
        if child_step:
            parent_step = child_step.parent
        else:
            return QtCore.QModelIndex()

        if parent_step:
            return self.index_by_step(parent_step)

        return QtCore.QModelIndex()

    def flags(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return 0

        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        if not self.is_read_only():
            step = self.step_for_index(index)
            if step:
                if not step.is_root():
                    flags |= QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEditable

                if step.can_have_children():
                    flags |= QtCore.Qt.ItemIsDropEnabled

        return flags

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def rowCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            # first level has only the root step
            return 1

        step = self.step_for_index(parent)
        return step.num_children() if step else 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        step = self.step_for_index(index)
        if not step:
            return

        if role == QtCore.Qt.DisplayRole:
            return step.get_display_name()

        elif role == QtCore.Qt.FontRole:
            font = QtGui.QFont()
            font.setItalic(self.is_read_only())
            return font

        elif role == QtCore.Qt.EditRole:
            return step.name

        elif role == QtCore.Qt.DecorationRole:
            icon_name: str
            if not step.is_action():
                if step.is_disabled_in_hierarchy():
                    icon_name = "step_group_disabled"
                elif step.has_warnings():
                    icon_name = "warning"
                else:
                    icon_name = "step_group"
            else:
                is_disabled = step.is_disabled_in_hierarchy()
                is_sym = step.action_proxy.is_mirrored
                if is_disabled:
                    if is_sym:
                        icon_name = "step_action_sym_disabled"
                    else:
                        icon_name = "step_action_disabled"
                elif step.has_warnings():
                    icon_name = "warning"
                else:
                    if is_sym:
                        icon_name = "step_action_sym"
                    else:
                        icon_name = "step_action"

            return QtGui.QIcon(f":/icon/{icon_name}.svg")

        elif role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(0, 20)

        elif role == QtCore.Qt.ForegroundRole:
            color = step.get_color()
            # dim color if step is disabled
            if step.is_disabled_in_hierarchy():
                color *= 0.4
            color.a = 1.0
            return QtGui.QColor(*color.as_8bit())

        elif role == QtCore.Qt.BackgroundRole:
            # highlight active step during interactive build
            if self.blueprint_model.is_interactive_building():
                if self.blueprint_model.interactive_builder.current_build_step_path == step.get_full_path():
                    return QtGui.QColor(60, 120, 94, 128)

            # highlight steps with warnings
            if step.is_action() and step.has_warnings():
                return QtGui.QColor(255, 205, 110, 25)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if self.is_read_only():
            return False
        if not index.isValid():
            return False

        step = self.step_for_index(index)

        if role == QtCore.Qt.EditRole:
            if not value:
                value = ""
            step_path = step.get_full_path()
            cmds.pulseRenameStep(step_path, value)
            return True

        elif role == QtCore.Qt.CheckStateRole:
            if step.is_root():
                return False
            step.is_disabled = True if value else False
            self.dataChanged.emit(index, index, [])
            self._emit_data_changed_on_all_children(index, [])
            # emit data changed on all children
            return True

        return False

    def _emit_data_changed_on_all_children(self, parent=QtCore.QModelIndex(), roles=None):
        if not parent.isValid():
            return
        row_count = self.rowCount(parent)
        if row_count == 0:
            return

        first_child = self.index(0, 0, parent)
        last_child = self.index(row_count - 1, 0, parent)

        # emit one event for all child indexes of parent
        self.dataChanged.emit(first_child, last_child, roles)

        # recursively emit on all children
        for i in range(row_count):
            child_index = self.index(i, 0, parent)
            self._emit_data_changed_on_all_children(child_index, roles)

    def _get_topmost_steps(self, indexes: List[QtCore.QModelIndex]) -> List[BuildStep]:
        steps = [self.step_for_index(index) for index in indexes]
        steps = [step for step in steps if step]
        steps = BuildStep.get_topmost_steps(steps)
        return steps

    def mimeTypes(self):
        return ["text/plain"]

    def mimeData(self, indexes):
        result = QtCore.QMimeData()

        top_steps = self._get_topmost_steps(indexes)
        step_data_list = [step.serialize() for step in top_steps]
        data_str = meta.encode_metadata(step_data_list)
        result.setData("text/plain", data_str.encode())
        return result

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def _get_step_data_list_from_mime_data(self, data: QtCore.QMimeData):
        data_str = data.data("text/plain").data().decode()
        if data_str:
            try:
                meta_data = meta.decode_metadata(data_str)
            except Exception as e:
                LOG.debug(e)
                return None
            else:
                if self.is_step_data(meta_data):
                    return meta_data
        return None

    def is_step_data(self, decoded_data):
        # TODO: implement to detect if the data is in a valid format
        return True

    def canDropMimeData(self, data: QtCore.QMimeData, action, row, column, parent_index):
        if action == QtCore.Qt.MoveAction or action == QtCore.Qt.CopyAction:
            step_data = self._get_step_data_list_from_mime_data(data)
            return step_data is not None

        return False

    def dropMimeData(self, data, action, row, column, parent_index):
        if not self.canDropMimeData(data, action, row, column, parent_index):
            return False

        if action == QtCore.Qt.IgnoreAction:
            return True

        step_data = self._get_step_data_list_from_mime_data(data)
        if step_data is None:
            # TODO: log error here, even though we shouldn't in canDropMimeData
            return False

        begin_row = 0
        parent_path = None

        if parent_index.isValid():
            parent_step = self.step_for_index(parent_index)
            if parent_step:
                if parent_step.can_have_children():
                    # drop into step group
                    begin_row = parent_step.num_children()
                    parent_path = parent_step.get_full_path()
                else:
                    # drop next to step
                    begin_row = parent_index.row()
                    parent_path = os.path.dirname(parent_step.get_full_path())

        if not parent_path:
            parent_path = ""
            begin_row = self.rowCount(QtCore.QModelIndex())
        if row != -1:
            begin_row = row

        cmds.undoInfo(openChunk=True, chunkName="Drag Pulse Actions")
        self._is_move_action_open = True
        cmds.evalDeferred(self._deferred_move_undo_close)

        count = len(step_data)
        for i in range(count):
            step_data_str = serialize_attr_value(step_data[i])
            new_step_path = cmds.pulseCreateStep(parent_path, begin_row + i, step_data_str)
            if new_step_path:
                new_step_path = new_step_path[0]

            if action == QtCore.Qt.MoveAction:
                # hacky, but because steps are removed after the new ones are created,
                # we need to rename the steps back to their original names in case they
                # were auto-renamed to avoid conflicts
                target_name = step_data[i].get("name", "")
                self._drag_rename_queue.append((new_step_path, target_name))

        # always return false, since we don't need the item view to handle removing moved items
        return True

    def removeRows(self, row, count, parent):
        indexes = []
        for i in range(row, row + count):
            index = self.index(i, 0, parent)
            indexes.append(index)

        # TODO: provide better api for deleting groups of steps
        top_steps = self._get_topmost_steps(indexes)

        paths = []
        for step in top_steps:
            path = step.get_full_path()
            if path:
                paths.append(path)

        if not self._is_move_action_open:
            cmds.undoInfo(openChunk=True, chunkName="Delete Pulse Actions")

        for path in paths:
            cmds.pulseDeleteStep(path)

        if not self._is_move_action_open:
            cmds.undoInfo(closeChunk=True)

    def _deferred_move_undo_close(self):
        """
        Called after a drag move operation has finished in order
        to capture all cmds into one undo chunk.
        """
        if self._is_move_action_open:
            self._is_move_action_open = False

            # rename dragged steps back to their original names
            # since they were changed due to conflicts during drop
            while self._drag_rename_queue:
                path, name = self._drag_rename_queue.pop()
                cmds.pulseRenameStep(path, name)

            cmds.undoInfo(closeChunk=True)


class BuildStepSelectionModel(QtCore.QItemSelectionModel):
    """
    The selection model for the BuildSteps of a Blueprint. Allows
    a singular selection that is shared across all UI for the Blueprint.
    An instance of this model should be acquired by going through
    the BlueprintUIModel for a specific Blueprint.
    """

    def get_selected_items(self) -> List[BuildStep]:
        """
        Return the currently selected BuildSteps
        """
        indexes = self.selectedIndexes()
        items: List[BuildStep] = []
        for index in indexes:
            if index.isValid():
                build_step: BuildStep = cast(BuildStepTreeModel, self.model).step_for_index(index)
                # buildStep = index.internalPointer()
                if build_step:
                    items.append(build_step)
        return list(set(items))

    def get_selected_groups(self):
        """
        Return indexes of the selected BuildSteps that can have children
        """
        indexes = self.selectedIndexes()
        result = []
        for index in indexes:
            if index.isValid():
                build_step: BuildStep = cast(BuildStepTreeModel, self.model).step_for_index(index)
                # buildStep = index.internalPointer()
                if build_step and build_step.can_have_children():
                    result.append(index)
                # TODO: get parent until we have an item that supports children
        return list(set(result))

    def get_selected_action(self):
        """
        Return the currently selected BuildAction, if any.
        """
        items = self.get_selected_items()
        return [i for i in items if isinstance(i, BuildAction)]

    def get_selected_item_paths(self):
        """
        Return the full paths of the selected BuildSteps
        """
        items = self.get_selected_items()
        return [i.get_full_path() for i in items]

    def set_selected_item_paths(self, paths):
        """
        Set the selection using BuildStep paths
        """
        if not self.model() or not hasattr(self.model(), "_blueprint"):
            return

        bp_model: BuildStepTreeModel = self.model()
        if not bp_model.blueprint:
            return

        steps = [bp_model.blueprint.get_step_by_path(p) for p in paths]
        indexes = [cast(BuildStepTreeModel, self.model()).index_by_step(s) for s in steps if s]
        self.clearSelection()
        for index in indexes:
            if index.isValid():
                self.select(index, QtCore.QItemSelectionModel.Select)
