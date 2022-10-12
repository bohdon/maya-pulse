"""
A panel for displaying Pulse and blueprint settings.
"""
import os

import pymel.core as pm

from pulse.vendor.Qt import QtWidgets
from .core import BlueprintUIModel, PulseWindow

from .gen.main_settings import Ui_MainSettings


class MainSettings(QtWidgets.QWidget):
    """
    A panel for displaying Pulse and blueprint settings.
    """

    def __init__(self, parent=None):
        super(MainSettings, self).__init__(parent=parent)

        self.blueprint_model = BlueprintUIModel.getDefaultModel()
        self.setEnabled(not self.blueprint_model.isReadOnly())
        self.model = self.blueprint_model.buildStepTreeModel

        self.ui = Ui_MainSettings()
        self.ui.setupUi(self)

        self.ui.file_path_text_label.setText(self._getSceneRelativeBlueprintFilePath())
        self.ui.rig_name_edit.setText(self.blueprint_model.blueprint.rigName)
        self.ui.rig_name_edit.textEdited.connect(self._onEditRigName)

        self.blueprint_model.rigNameChanged.connect(self._onRigNameChanged)
        self.blueprint_model.fileChanged.connect(self._onFileChanged)
        self.blueprint_model.readOnlyChanged.connect(self._onReadOnlyChanged)

    def _onFileChanged(self):
        """
        Called when a blueprint is created, opened, or saved to a new path.
        """
        self.ui.file_path_text_label.setText(self._getSceneRelativeBlueprintFilePath())

    def _onEditRigName(self):
        self.blueprint_model.setRigName(self.ui.rig_name_edit.text())

    def _onRigNameChanged(self, name):
        self.ui.rig_name_edit.setText(name)

    def _onReadOnlyChanged(self, isReadOnly):
        self.setEnabled(not isReadOnly)

    def _getSceneRelativeBlueprintFilePath(self):
        return self._getSceneRelativeFilePath(self.blueprint_model.getBlueprintFilePath())

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
