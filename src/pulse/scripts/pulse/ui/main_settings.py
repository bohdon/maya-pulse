"""
A panel for displaying Pulse and blueprint settings.
"""
import os

import pymel.core as pm

from . import utils
from .core import BlueprintUIModel, PulseWindow
from .gen.main_settings import Ui_MainSettings
from ..core import BlueprintSettings, BuildActionPackageRegistry
from ..vendor.Qt import QtCore, QtGui, QtWidgets


class ActionPackagesList(QtWidgets.QWidget):
    """
    Displays the list of action packages in the BuildActionPackagesRegistry.
    """

    def __init__(self, parent=None):
        super(ActionPackagesList, self).__init__(parent=parent)

        self.setup_ui(self)
        self._update_package_list()

    def setup_ui(self, parent):
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def _update_package_list(self):
        utils.clear_layout(self.layout)

        registry = BuildActionPackageRegistry.get()

        for package in registry.action_packages:
            label = QtWidgets.QLabel(self)
            label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
            label.setProperty("cssClasses", "block")
            label.setText(self.get_package_display_name(package))
            self.layout.addWidget(label)

    def get_package_display_name(self, package):
        return f"{package.__name__} ({package.__path__[0]})"

    def showEvent(self, event: QtGui.QShowEvent):
        super(ActionPackagesList, self).showEvent(event)

        self._update_package_list()


class MainSettings(QtWidgets.QWidget):
    """
    A panel for displaying Pulse and blueprint settings.
    """

    def __init__(self, parent=None):
        super(MainSettings, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.get_default_model()
        self.model = self.blueprintModel.build_step_tree_model

        self.ui = Ui_MainSettings()
        self.ui.setupUi(self)

        action_pkgs = ActionPackagesList(self)
        self.ui.action_pkgs_layout.addWidget(action_pkgs)

        self.ui.file_path_text_label.setText(self._get_scene_relative_blueprint_file_path())
        self._update_all_setting_values()
        self.ui.config_file_path_label.setText(self.blueprintModel.blueprint.config.file_path)

        self.ui.name_edit.textEdited.connect(self._on_edit_name)
        self.ui.debug_build_check.stateChanged.connect(self._on_edit_debug_build)

        self.blueprintModel.setting_changed.connect(self._on_setting_changed)
        self.blueprintModel.file_changed.connect(self._on_file_changed)
        self.blueprintModel.read_only_changed.connect(self._on_read_only_changed)

        self._on_read_only_changed(self.blueprintModel.is_read_only())

    def _update_all_setting_values(self):
        self.ui.name_edit.setText(self.blueprintModel.get_setting(BlueprintSettings.NAME))

    def _on_file_changed(self):
        """
        Called when a blueprint is created, opened, or saved to a new path.
        """
        self.ui.file_path_text_label.setText(self._get_scene_relative_blueprint_file_path())
        # if blueprint changed then all settings should be refreshed
        self._update_all_setting_values()

    def _on_edit_name(self):
        self.blueprintModel.set_setting(BlueprintSettings.NAME, self.ui.name_edit.text())

    def _on_edit_debug_build(self):
        self.blueprintModel.set_setting(BlueprintSettings.DEBUG_BUILD, self.ui.debug_build_check.isChecked())

    def _on_setting_changed(self, key: str, value: object):
        if key == BlueprintSettings.NAME:
            self.ui.name_edit.setText(str(value))

    def _on_read_only_changed(self, is_read_only):
        self.ui.blueprint_tab.setEnabled(not is_read_only)

    def _get_scene_relative_blueprint_file_path(self):
        return self._get_scene_relative_file_path(self.blueprintModel.get_blueprint_file_path())

    @staticmethod
    def _get_scene_relative_file_path(file_path):
        # get the file name relative to the current scene name
        return file_path
        scene_path = pm.sceneName()
        if scene_path:
            scene_dir = scene_path.dirname()
            rel_path = os.path.relpath(file_path, scene_dir)
            return rel_path

        return file_path


class MainSettingsWindow(PulseWindow):
    """
    The settings window for Pulse and the current blueprint.
    """

    OBJECT_NAME = "pulseMainSettingsWindow"
    WINDOW_MODULE = "pulse.ui.main_settings"
    WINDOW_TITLE = "Pulse Settings"
    WIDGET_CLASS = MainSettings
