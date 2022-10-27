"""
Toolbar for running main actions like validate and build.
"""

import logging

import maya.cmds as cmds

from ..vendor.Qt import QtWidgets
from ..blueprints import BlueprintSettings
from .core import BlueprintUIModel
from .main_settings import MainSettingsWindow
from .actioneditor import ActionEditorWindow
from .designtoolkit import DesignToolkitWindow

from .gen.main_toolbar import Ui_MainToolbar

LOG = logging.getLogger(__name__)


class MainToolbar(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(MainToolbar, self).__init__(parent=parent)

        # used to cause a latent refresh after builds
        self._isStateDirty = False

        self.blueprint_model = BlueprintUIModel.getDefaultModel()

        self.ui = Ui_MainToolbar()
        self.ui.setupUi(self)

        self._cleanState()
        self._updateMode()
        self._updateRigName()

        # connect signals
        self.blueprint_model.changeSceneFinished.connect(self._onChangeSceneFinished)
        self.blueprint_model.fileChanged.connect(self._onFileChanged)
        self.blueprint_model.isFileModifiedChanged.connect(self._onFileModifiedChanged)
        self.blueprint_model.rigExistsChanged.connect(self._onRigExistsChanged)
        self.blueprint_model.readOnlyChanged.connect(self._onReadOnlyChanged)
        self.blueprint_model.settingChanged.connect(self._onSettingChanged)

        # TODO (bsayre): use blueprint model to track interactive build

        self.ui.new_blueprint_btn.clicked.connect(self.blueprint_model.newFile)
        self.ui.validate_btn.clicked.connect(self.blueprint_model.run_validation)
        self.ui.build_btn.clicked.connect(self.blueprint_model.run_build)
        self.ui.interactive_build_btn.clicked.connect(self.blueprint_model.run_or_step_interactive_build)
        self.ui.open_blueprint_btn.clicked.connect(self.blueprint_model.open_rig_blueprint)

        self.ui.settings_btn.clicked.connect(MainSettingsWindow.toggleWindow)
        self.ui.design_toolkit_btn.clicked.connect(DesignToolkitWindow.toggleWindow)
        self.ui.action_editor_btn.clicked.connect(ActionEditorWindow.toggleWindow)

    def doesRigExist(self):
        return self.blueprint_model.doesRigExist

    def showEvent(self, event):
        super(MainToolbar, self).showEvent(event)
        self._onStateDirty()

    def _onChangeSceneFinished(self):
        self._updateMode()
        self._updateRigName()

    def _onFileChanged(self):
        self._updateMode()
        self._updateRigName()

    def _onFileModifiedChanged(self, isModified):
        self._updateRigName()

    def _onSettingChanged(self, key: str, value: object):
        if key == BlueprintSettings.RIG_NAME:
            self._updateRigName()

    def _updateRigName(self):
        # prevent updating rig and file name while changing scenes
        if self.blueprint_model.isChangingScenes:
            return

        fileName = self.blueprint_model.getBlueprintFileName()
        if fileName is None:
            fileName = 'untitled'
        if self.blueprint_model.isFileModified():
            fileName += '*'

        self.ui.rig_name_label.setText(self.blueprint_model.getSetting(BlueprintSettings.RIG_NAME))
        self.ui.blueprint_file_name_label.setText(fileName)
        self.ui.blueprint_file_name_label.setToolTip(self.blueprint_model.getBlueprintFilePath())

    def _onRigExistsChanged(self):
        self._cleanState()
        self._updateMode()

    def _onReadOnlyChanged(self, isReadOnly):
        # TODO: represent read-only state somewhere
        pass

    def _cleanState(self):
        self._isStateDirty = False
        self.setEnabled(True)  # TODO: True if isBuilding

    def _onStateDirty(self):
        if not self._isStateDirty:
            self._isStateDirty = True
            self.setEnabled(False)
            cmds.evalDeferred(self._cleanState)

    def _updateMode(self):
        """
        Update the mode header and visible page, blueprint or rig.
        """
        # prevent mode changes while changing scenes to avoid flickering
        # since a file may be briefly closed before a new one is opened
        if self.blueprint_model.isChangingScenes:
            return

        if self.blueprint_model.isFileOpen():
            self.ui.main_stack.setCurrentWidget(self.ui.opened_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.new_page)

        if self.doesRigExist():
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

        can_interactive_build = self.blueprint_model.is_interactive_building() or not self.doesRigExist()
        self.ui.interactive_build_btn.setEnabled(can_interactive_build)

        # refresh stylesheet for mode frame
        self.ui.mode_frame.setStyleSheet('')
