"""
A panel for displaying Pulse and blueprint settings.
"""
import os

import pymel.core as pm

from pulse.vendor.Qt import QtWidgets
from .core import BlueprintUIModel, PulseWindow

from .gen.main_settings import Ui_MainSettings
from ..blueprints import BlueprintSettings


class MainSettings(QtWidgets.QWidget):
    """
    A panel for displaying Pulse and blueprint settings.
    """

    def __init__(self, parent=None):
        super(MainSettings, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.setEnabled(not self.blueprintModel.isReadOnly())
        self.model = self.blueprintModel.buildStepTreeModel

        self.ui = Ui_MainSettings()
        self.ui.setupUi(self)

        self.ui.file_path_text_label.setText(self._getSceneRelativeBlueprintFilePath())
        self._updateAllSettingValues()

        self.ui.rig_name_edit.textEdited.connect(self._onEditRigName)
        self.ui.rig_node_fmt_edit.textEdited.connect(self._onEditRigNodeNameFormat)

        self.blueprintModel.settingChanged.connect(self._onSettingChanged)
        self.blueprintModel.fileChanged.connect(self._onFileChanged)
        self.blueprintModel.readOnlyChanged.connect(self._onReadOnlyChanged)

    def _updateAllSettingValues(self):
        self.ui.rig_name_edit.setText(self.blueprintModel.getSetting(BlueprintSettings.RIG_NAME))
        self.ui.rig_node_fmt_edit.setText(self.blueprintModel.getSetting(BlueprintSettings.RIG_NODE_NAME_FORMAT))

    def _onFileChanged(self):
        """
        Called when a blueprint is created, opened, or saved to a new path.
        """
        self.ui.file_path_text_label.setText(self._getSceneRelativeBlueprintFilePath())
        # if blueprint changed then all settings should be refreshed
        self._updateAllSettingValues()

    def _onEditRigName(self):
        self.blueprintModel.setSetting(BlueprintSettings.RIG_NAME, self.ui.rig_name_edit.text())

    def _onEditRigNodeNameFormat(self):
        self.blueprintModel.setSetting(BlueprintSettings.RIG_NODE_NAME_FORMAT, self.ui.rig_node_fmt_edit.text())

    def _onSettingChanged(self, key: str, value: object):
        if key == BlueprintSettings.RIG_NAME:
            self.ui.rig_name_edit.setText(str(value))
        elif key == BlueprintSettings.RIG_NODE_NAME_FORMAT:
            self.ui.rig_node_fmt_edit.setText(str(value))

    def _onReadOnlyChanged(self, isReadOnly):
        self.setEnabled(not isReadOnly)

    def _getSceneRelativeBlueprintFilePath(self):
        return self._getSceneRelativeFilePath(self.blueprintModel.getBlueprintFilePath())

    @staticmethod
    def _getSceneRelativeFilePath(file_path):
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
    OBJECT_NAME = 'pulseMainSettingsWindow'
    WINDOW_MODULE = 'pulse.ui.main_settings'
    WINDOW_TITLE = 'Pulse Settings'
    WIDGET_CLASS = MainSettings
