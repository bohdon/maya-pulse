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

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.blueprintModel.rigExistsChanged.connect(self._onRigExistsChanged)

        self.ui = Ui_MainToolbar()
        self.ui.setupUi(self)

        self._cleanState()
        self._updateMode()
        self._updateRigName()

        # connect signals
        self.blueprintModel.fileChanged.connect(self._onFileChanged)
        self.blueprintModel.isFileModifiedChanged.connect(self._onFileModifiedChanged)
        self.blueprintModel.readOnlyChanged.connect(self._onReadOnlyChanged)
        self.blueprintModel.rigNameChanged.connect(self._onRigNameChanged)

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

    def _onFileChanged(self):
        self._updateMode()

    def _onFileModifiedChanged(self, isModified):
        self._updateRigName()

    def _onRigNameChanged(self, name):
        self._updateRigName()

    def _updateRigName(self):
        fileName = self.blueprintModel.getBlueprintFileName()
        if fileName is None:
            fileName = 'untitled'
        if self.blueprintModel.isFileModified():
            fileName += '*'

        self.ui.rig_name_label.setText(self.blueprintModel.blueprint.rigName)
        self.ui.blueprint_file_name_label.setText(fileName)
        self.ui.blueprint_file_name_label.setToolTip(self.blueprintModel.getBlueprintFilePath())

    def _onRigExistsChanged(self):
        self._cleanState()
        self._updateMode()

    def _onReadOnlyChanged(self, is_read_only):
        # TODO: represent read-only state somewhere
        pass

    def _cleanState(self):
        self.isStateDirty = False
        self.setEnabled(True)  # TODO: True if isBuilding

    def _onStateDirty(self):
        if not self.isStateDirty:
            self.isStateDirty = True
            self.setEnabled(False)
            cmds.evalDeferred(self._cleanState)

    def _updateMode(self):
        """
        Update the mode header and visible page, blueprint or rig.
        """
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
            if not BlueprintBuilder.preBuildValidate(blueprint):
                return

            validator = BlueprintValidator(blueprint, debug=True)
            validator.start()

    def runBuild(self):
        blueprint = self.blueprintModel.blueprint
        if blueprint is not None:
            if not BlueprintBuilder.preBuildValidate(blueprint):
                return

            # TODO: expose prompt to save scene as option
            if not editorutils.saveSceneIfDirty(prompt=False):
                return

            # if auto_save:
            self.blueprintModel.saveFile()

            builder = BlueprintBuilder.createBuilderWithCurrentScene(
                blueprint, debug=True)
            builder.showProgressUI = True
            builder.start()

            cmds.evalDeferred(self._onStateDirty)

            # TODO: add build events for situations like this
            cmds.evalDeferred(self.blueprintModel.reloadFile, low=True)
