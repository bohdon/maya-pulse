"""
Toolbar for running main actions like validate and build.
"""

import logging

import maya.cmds as cmds

from ..vendor.Qt import QtWidgets
from .. import editorutils
from ..blueprints import BlueprintBuilder, BlueprintValidator, BlueprintSettings
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

        # used to cause a latent refresh after builds
        self._isStateDirty = False

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        self.ui = Ui_MainToolbar()
        self.ui.setupUi(self)

        self._cleanState()
        self._updateMode()
        self._updateRigName()

        # connect signals
        self.blueprintModel.changeSceneFinished.connect(self._onChangeSceneFinished)
        self.blueprintModel.fileChanged.connect(self._onFileChanged)
        self.blueprintModel.isFileModifiedChanged.connect(self._onFileModifiedChanged)
        self.blueprintModel.rigExistsChanged.connect(self._onRigExistsChanged)
        self.blueprintModel.readOnlyChanged.connect(self._onReadOnlyChanged)
        self.blueprintModel.settingChanged.connect(self._onSettingChanged)

        self.ui.new_blueprint_btn.clicked.connect(self.blueprintModel.newFile)
        self.ui.validate_btn.clicked.connect(self.runValidation)
        self.ui.build_btn.clicked.connect(self.runBuild)
        self.ui.open_blueprint_btn.clicked.connect(openFirstRigBlueprint)

        self.ui.settings_btn.clicked.connect(MainSettingsWindow.toggleWindow)
        self.ui.design_toolkit_btn.clicked.connect(DesignToolkitWindow.toggleWindow)
        self.ui.action_editor_btn.clicked.connect(ActionEditorWindow.toggleWindow)

    def doesRigExist(self):
        return self.blueprintModel.doesRigExist

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
        if self.blueprintModel.isChangingScenes:
            return

        fileName = self.blueprintModel.getBlueprintFileName()
        if fileName is None:
            fileName = 'untitled'
        if self.blueprintModel.isFileModified():
            fileName += '*'

        self.ui.rig_name_label.setText(self.blueprintModel.getSetting(BlueprintSettings.RIG_NAME))
        self.ui.blueprint_file_name_label.setText(fileName)
        self.ui.blueprint_file_name_label.setToolTip(self.blueprintModel.getBlueprintFilePath())

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
        if self.blueprintModel.isChangingScenes:
            return

        if self.blueprintModel.isFileOpen():
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

        # refresh stylesheet for mode frame
        self.ui.mode_frame.setStyleSheet('')

    def runValidation(self):
        blueprint = self.blueprintModel.blueprint
        if blueprint is not None:
            if not BlueprintBuilder.pre_build_validate(blueprint):
                return

            validator = BlueprintValidator(blueprint)
            validator.start()

    def runBuild(self):
        blueprint = self.blueprintModel.blueprint
        if blueprint is not None:
            if not BlueprintBuilder.pre_build_validate(blueprint):
                return

            # save maya scene
            # TODO: expose prompt to save scene as option
            if not editorutils.saveSceneIfDirty(prompt=False):
                return

            # save blueprint
            if self.blueprintModel.isFileModified():
                if not self.blueprintModel.saveFileWithPrompt():
                    return

            builder = BlueprintBuilder.from_current_scene(blueprint)
            builder.show_progress_ui = True
            builder.start()

            cmds.evalDeferred(self._onStateDirty)

            # TODO: add build events for situations like this
            cmds.evalDeferred(self.blueprintModel.refreshRigExists, low=True)
