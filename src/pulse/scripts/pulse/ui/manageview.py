"""
A panel for displaying blueprint attributes and details
"""
import os

import pymel.core as pm

from pulse.vendor.Qt import QtWidgets
from .core import BlueprintUIModel

from .gen.blueprint_settings import Ui_BlueprintSettings


class ManageWidget(QtWidgets.QWidget):
    """
    A panel for displaying blueprint attributes and details
    """

    def __init__(self, parent=None):
        super(ManageWidget, self).__init__(parent=parent)

        self.blueprint_model = BlueprintUIModel.getDefaultModel()
        self.setEnabled(not self.blueprint_model.isReadOnly())
        self.model = self.blueprint_model.buildStepTreeModel

        self.ui = Ui_BlueprintSettings()
        self.ui.setupUi(self)

        self.ui.file_path_edit.setText(self._get_scene_relative_file_path(self.blueprint_model.getBlueprintFilepath()))
        self.ui.rig_name_edit.setText(self.blueprint_model.getRigName())
        self.ui.rig_name_edit.textChanged.connect(self._on_edit_rig_name)

        self.blueprint_model.rigNameChanged.connect(self._on_rig_name_changed)
        self.blueprint_model.fileChanged.connect(self._on_file_path_changed)
        self.blueprint_model.readOnlyChanged.connect(self._on_read_only_changed)

    def _on_file_path_changed(self):
        self.ui.file_path_edit.setText(self._get_scene_relative_file_path(self.blueprint_model.getBlueprintFilepath()))

    def _on_edit_rig_name(self):
        self.blueprint_model.setRigName(self.ui.rig_name_edit.text())

    def _on_rig_name_changed(self, name):
        self.ui.rig_name_edit.setText(name)

    def _on_read_only_changed(self, is_read_only):
        self.setEnabled(not is_read_only)

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
