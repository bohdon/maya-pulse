"""
Toolbar for running main actions like validate and build.
"""

import logging

import maya.cmds as cmds

from ..vendor.Qt import QtWidgets
from .. import editorutils
from ..blueprints import BlueprintBuilder, BlueprintValidator
from ..rigs import openFirstRigBlueprint
from .core import BlueprintUIModel
from .main_settings import MainSettingsWindow
from .actioneditor import ActionEditorWindow
from .designtoolkit import DesignToolkitWindow

from .gen.main_toolbar import Ui_MainToolbar

LOG = logging.getLogger(__name__)


class MainToolbar(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainToolbar, self).__init__(parent=parent)

        self.isStateDirty = False

        self.blueprint_model = BlueprintUIModel.getDefaultModel()
        self.blueprint_model.rigExistsChanged.connect(self._on_rig_exists_changed)

        self.ui = Ui_MainToolbar()
        self.ui.setupUi(self)

        self._clean_state()
        self._update_mode()
        self._update_rig_name()

        # connect signals
        self.blueprint_model.readOnlyChanged.connect(self._on_read_only_changed)
        self.blueprint_model.rigNameChanged.connect(self._on_rig_name_changed)

        self.ui.validate_btn.clicked.connect(self.run_validation)
        self.ui.build_btn.clicked.connect(self.run_build)
        self.ui.open_blueprint_btn.clicked.connect(openFirstRigBlueprint)

        self.ui.settings_btn.clicked.connect(MainSettingsWindow.toggleWindow)
        self.ui.design_toolkit_btn.clicked.connect(DesignToolkitWindow.toggleWindow)
        self.ui.action_editor_btn.clicked.connect(ActionEditorWindow.toggleWindow)

    @property
    def does_rig_exist(self):
        return self.blueprint_model.doesRigExist

    def showEvent(self, event):
        super(MainToolbar, self).showEvent(event)
        self._on_state_dirty()

    def _on_rig_name_changed(self, name):
        self._update_rig_name()

    def _update_rig_name(self):
        self.ui.rig_name_label.setText(self.blueprint_model.blueprint.rigName)
        self.ui.blueprint_file_name_label.setText(self.blueprint_model.getBlueprintFileName())
        self.ui.blueprint_file_name_label.setToolTip(self.blueprint_model.getBlueprintFilePath())

    def _on_rig_exists_changed(self):
        self._clean_state()
        self._update_mode()

    def _on_read_only_changed(self, is_read_only):
        # TODO: represent read-only state elsewhere
        self._update_mode()

    def _clean_state(self):
        self.isStateDirty = False
        self.setEnabled(True)  # TODO: True if isBuilding

    def _on_state_dirty(self):
        if not self.isStateDirty:
            self.isStateDirty = True
            self.setEnabled(False)
            cmds.evalDeferred(self._clean_state)

    def _update_mode(self):
        """
        Update the mode header and visible page, blueprint or rig.
        """
        if self.does_rig_exist:
            # rig read-only mode
            self.ui.validate_btn.setEnabled(False)
            self.ui.build_btn.setEnabled(False)
            self.ui.open_blueprint_btn.setEnabled(True)
            # switch active model label
            self.ui.blueprint_mode_label.setEnabled(False)
            self.ui.rig_mode_label.setEnabled(True)
            # update mode frame color
            self.ui.mode_frame.setProperty('cssClasses', 'toolbar-rig')
        else:
            # blueprint editing mode
            self.ui.validate_btn.setEnabled(True)
            self.ui.build_btn.setEnabled(True)
            self.ui.open_blueprint_btn.setEnabled(False)
            # switch active model label
            self.ui.blueprint_mode_label.setEnabled(True)
            self.ui.rig_mode_label.setEnabled(False)
            # update mode frame color
            self.ui.mode_frame.setProperty('cssClasses', 'toolbar-blueprint')

        # refresh stylesheet for mode frame
        self.ui.mode_frame.setStyleSheet('')

    def run_validation(self):
        blueprint = self.blueprint_model.blueprint
        if blueprint is not None:
            if not BlueprintBuilder.preBuildValidate(blueprint):
                return

            validator = BlueprintValidator(blueprint, debug=True)
            validator.start()

    def run_build(self):
        blueprint = self.blueprint_model.blueprint
        if blueprint is not None:
            if not BlueprintBuilder.preBuildValidate(blueprint):
                return

            # TODO: expose prompt to save scene as option
            if not editorutils.saveSceneIfDirty(prompt=False):
                return

            # if auto_save:
            self.blueprint_model.saveFile()

            builder = BlueprintBuilder.createBuilderWithCurrentScene(
                blueprint, debug=True)
            builder.showProgressUI = True
            builder.start()

            cmds.evalDeferred(self._on_state_dirty)

            # TODO: add build events for situations like this
            cmds.evalDeferred(self.blueprint_model.reloadFile, low=True)
