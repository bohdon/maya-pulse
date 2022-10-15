"""
A panel for displaying Pulse and blueprint settings.
"""
import os

import pymel.core as pm

from pulse.vendor.Qt import QtCore, QtGui, QtWidgets
from ..blueprints import BlueprintSettings
from ..loader import BuildActionPackageRegistry
from . import utils
from .core import BlueprintUIModel, PulseWindow
from .gen.main_settings import Ui_MainSettings


class ActionPackagesList(QtWidgets.QWidget):
    """
    Displays the list of action packages in the BuildActionPackagesRegistry.
    """

    def __init__(self, parent=None):
        super(ActionPackagesList, self).__init__(parent=parent)

        self._labelStylesheet = 'background-color: rgba(255, 255, 255, 5%); border-radius: 2px; padding: 2px'

        self.setupUi(self)
        self._updatePackageList()

    def setupUi(self, parent):
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.layout.setMargin(0)

    def _updatePackageList(self):
        utils.clearLayout(self.layout)

        registry = BuildActionPackageRegistry.get()

        for package in registry.action_packages:
            label = QtWidgets.QLabel(self)
            label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
            label.setStyleSheet(self._labelStylesheet)
            label.setText(self.getPackageDisplayName(package))
            self.layout.addWidget(label)

        for actions_dir in registry.action_dirs:
            label = QtWidgets.QLabel(self)
            label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
            label.setStyleSheet(self._labelStylesheet)
            label.setText(actions_dir)
            self.layout.addWidget(label)

    def getPackageDisplayName(self, package):
        return f'{package.__name__} ({package.__path__[0]})'

    def showEvent(self, event: QtGui.QShowEvent):
        super(ActionPackagesList, self).showEvent(event)

        self._updatePackageList()


class MainSettings(QtWidgets.QWidget):
    """
    A panel for displaying Pulse and blueprint settings.
    """

    def __init__(self, parent=None):
        super(MainSettings, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel

        self.ui = Ui_MainSettings()
        self.ui.setupUi(self)

        action_pkgs = ActionPackagesList(self)
        self.ui.action_pkgs_layout.addWidget(action_pkgs)

        self.ui.file_path_text_label.setText(self._getSceneRelativeBlueprintFilePath())
        self._updateAllSettingValues()

        self.ui.rig_name_edit.textEdited.connect(self._onEditRigName)
        self.ui.rig_node_fmt_edit.textEdited.connect(self._onEditRigNodeNameFormat)
        self.ui.debug_build_check.stateChanged.connect(self._onEditDebugBuild)

        self.blueprintModel.settingChanged.connect(self._onSettingChanged)
        self.blueprintModel.fileChanged.connect(self._onFileChanged)
        self.blueprintModel.readOnlyChanged.connect(self._onReadOnlyChanged)

        self._onReadOnlyChanged(self.blueprintModel.isReadOnly())

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

    def _onEditDebugBuild(self):
        self.blueprintModel.setSetting(BlueprintSettings.DEBUG_BUILD, self.ui.debug_build_check.isChecked())

    def _onSettingChanged(self, key: str, value: object):
        if key == BlueprintSettings.RIG_NAME:
            self.ui.rig_name_edit.setText(str(value))
        elif key == BlueprintSettings.RIG_NODE_NAME_FORMAT:
            self.ui.rig_node_fmt_edit.setText(str(value))

    def _onReadOnlyChanged(self, isReadOnly):
        self.ui.blueprint_tab.setEnabled(not isReadOnly)

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
