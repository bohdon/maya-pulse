"""
Toolbar for running main actions like validate and build.
"""

import logging

import maya.cmds as cmds

from ..vendor.Qt import QtGui, QtWidgets
from ..core import BlueprintSettings
from . import utils
from .core import BlueprintUIModel
from .main_settings import MainSettingsWindow
from .action_editor import ActionEditorWindow
from .designtoolkit import DesignToolkitWindow

from .gen.main_toolbar import Ui_MainToolbar

LOG = logging.getLogger(__name__)


class MainToolbar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainToolbar, self).__init__(parent=parent)

        # used to cause a latent refresh after builds
        self._isStateDirty = False

        self.blueprint_model = BlueprintUIModel.get_default_model()

        self.ui = Ui_MainToolbar()
        self.ui.setupUi(self)
        utils.set_custom_context_menu(self.ui.build_btn, self._show_build_context_menu)

        self._clean_state()
        self._update_mode()
        self._update_rig_name()

        # connect signals
        self.blueprint_model.change_scene_finished.connect(self._on_change_scene_finished)
        self.blueprint_model.file_changed.connect(self._on_file_changed)
        self.blueprint_model.is_file_modified_changed.connect(self._on_file_modified_changed)
        self.blueprint_model.rig_exists_changed.connect(self._on_rig_exists_changed)
        self.blueprint_model.read_only_changed.connect(self._on_read_only_changed)
        self.blueprint_model.setting_changed.connect(self._on_setting_changed)

        self.ui.new_blueprint_btn.clicked.connect(self.blueprint_model.new_file)
        self.ui.validate_btn.clicked.connect(self.blueprint_model.run_validation)
        self.ui.build_btn.clicked.connect(self.blueprint_model.run_build)
        self.ui.interactive_next_btn.clicked.connect(self.blueprint_model.interactive_build_next_action)
        self.ui.interactive_next_step_btn.clicked.connect(self.blueprint_model.interactive_build_next_step)
        self.ui.interactive_continue_btn.clicked.connect(self.blueprint_model.continue_interactive_build)
        self.ui.open_blueprint_btn.clicked.connect(self.blueprint_model.open_rig_blueprint)

        self.ui.settings_btn.clicked.connect(MainSettingsWindow.toggleWindow)
        self.ui.design_toolkit_btn.clicked.connect(DesignToolkitWindow.toggleWindow)
        self.ui.action_editor_btn.clicked.connect(ActionEditorWindow.toggleWindow)

    def _show_build_context_menu(self, position):
        menu = QtWidgets.QMenu()
        interactive_action = menu.addAction("Interactive Build")
        interactive_action.setStatusTip("Start an interactive build that can be stepped through incrementally.")
        interactive_action.triggered.connect(self.blueprint_model.run_interactive_build)
        interactive_action.setEnabled(self.blueprint_model.can_interactive_build())
        menu.exec_(self.ui.build_btn.mapToGlobal(position))

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super(MainToolbar, self).mousePressEvent(event)

    def does_rig_exist(self):
        return self.blueprint_model.does_rig_exist

    def showEvent(self, event):
        super(MainToolbar, self).showEvent(event)
        self._on_state_dirty()

    def _on_change_scene_finished(self):
        self._update_mode()
        self._update_rig_name()

    def _on_file_changed(self):
        self._update_mode()
        self._update_rig_name()

    def _on_file_modified_changed(self, is_modified):
        self._update_rig_name()

    def _on_setting_changed(self, key: str, value: object):
        if key == BlueprintSettings.RIG_NAME:
            self._update_rig_name()

    def _update_rig_name(self):
        # prevent updating rig and file name while changing scenes
        if self.blueprint_model.is_changing_scenes:
            return

        file_name = self.blueprint_model.get_blueprint_file_name()
        if file_name is None:
            file_name = "untitled"
        if self.blueprint_model.is_file_modified():
            file_name += "*"

        self.ui.rig_name_label.setText(self.blueprint_model.get_setting(BlueprintSettings.RIG_NAME))
        self.ui.blueprint_file_name_label.setText(file_name)
        self.ui.blueprint_file_name_label.setToolTip(self.blueprint_model.get_blueprint_file_path())

    def _on_rig_exists_changed(self):
        self._clean_state()
        self._update_mode()

    def _on_read_only_changed(self, is_read_only):
        # TODO: represent read-only state somewhere
        pass

    def _clean_state(self):
        self._isStateDirty = False
        self.setEnabled(True)  # TODO: True if isBuilding

    def _on_state_dirty(self):
        if not self._isStateDirty:
            self._isStateDirty = True
            self.setEnabled(False)
            cmds.evalDeferred(self._clean_state)

    def _update_mode(self):
        """
        Update the mode header and visible page, blueprint or rig.
        """
        # prevent mode changes while changing scenes to avoid flickering
        # since a file may be briefly closed before a new one is opened
        if self.blueprint_model.is_changing_scenes:
            return

        if self.blueprint_model.is_file_open():
            self.ui.main_stack.setCurrentWidget(self.ui.opened_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.new_page)

        if self.does_rig_exist():
            # rig read-only mode
            self.ui.validate_btn.setEnabled(False)
            self.ui.build_btn.setEnabled(False)
            self.ui.open_blueprint_btn.setEnabled(True)
            # switch active model label
            self.ui.blueprint_mode_label.setEnabled(False)
            self.ui.rig_mode_label.setEnabled(True)
            # update mode frame color
            self.ui.mode_frame.setProperty("cssClasses", "toolbar-rig")
        else:
            # blueprint editing mode
            self.ui.validate_btn.setEnabled(True)
            self.ui.build_btn.setEnabled(True)
            self.ui.open_blueprint_btn.setEnabled(False)
            # switch active model label
            self.ui.blueprint_mode_label.setEnabled(True)
            self.ui.rig_mode_label.setEnabled(False)
            # update mode frame color
            self.ui.mode_frame.setProperty("cssClasses", "toolbar-blueprint")

        if self.blueprint_model.is_interactive_building():
            # show button to step interactive build forward
            self.ui.interactive_build_frame.setVisible(True)
        else:
            self.ui.interactive_build_frame.setVisible(False)

        # refresh stylesheet for mode frame
        self.ui.mode_frame.setStyleSheet("")
