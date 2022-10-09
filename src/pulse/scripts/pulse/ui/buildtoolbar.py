"""
Toolbar for running main actions like validate and build.
"""

import logging

import maya.cmds as cmds

from .core import BlueprintUIModel
from .actioneditor import ActionEditorWindow
from .designtoolkit import DesignToolkitWindow
from .style import UIColors
from .. import editorutils
from ..blueprints import BlueprintBuilder, BlueprintValidator
from ..rigs import openFirstRigBlueprint
from ..vendor.Qt import QtWidgets, QtGui

LOG = logging.getLogger(__name__)


class BuildToolbarWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(BuildToolbarWidget, self).__init__(parent=parent)

        self.isStateDirty = False

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.blueprintModel.rigExistsChanged.connect(self.onRigExistsChanged)

        self.setupUi(self)
        self.onRigExistsChanged()

        # connect signals
        self.blueprintModel.readOnlyChanged.connect(self.onReadOnlyChanged)
        self.blueprintModel.rigNameChanged.connect(self.rigNameChanged)

    @property
    def rigExists(self):
        return self.blueprintModel.rigExists

    def showEvent(self, event):
        super(BuildToolbarWidget, self).showEvent(event)
        self.onStateDirty()

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        self.frame = QtWidgets.QFrame(parent)
        self.frame.setObjectName("panelFrame")
        layout.addWidget(self.frame)

        hlayout = QtWidgets.QHBoxLayout(self.frame)

        labelLayout = QtWidgets.QVBoxLayout(parent)
        hlayout.addLayout(labelLayout)

        font = QtGui.QFont()
        font.setPointSize(12)
        font.setWeight(75)
        font.setBold(True)
        self.rigNameLabel = QtWidgets.QLabel(parent)
        self.rigNameLabel.setFont(font)
        self.rigNameLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.rigNameLabel.setText(self.getRigNameText(
            self.blueprintModel.getRigName()))
        labelLayout.addWidget(self.rigNameLabel)

        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(True)
        self.rigOrBlueprintLabel = QtWidgets.QLabel(parent)
        self.rigOrBlueprintLabel.setFont(font)
        labelLayout.addWidget(self.rigOrBlueprintLabel)

        self.design_toolkit_btn = QtWidgets.QPushButton(parent)
        self.design_toolkit_btn.setText("D")
        self.design_toolkit_btn.setFixedSize(24, 24)
        self.design_toolkit_btn.clicked.connect(DesignToolkitWindow.toggleWindow)
        hlayout.addWidget(self.design_toolkit_btn)

        self.action_editor_btn = QtWidgets.QPushButton(parent)
        self.action_editor_btn.setText("A")
        self.action_editor_btn.setFixedSize(24, 24)
        self.action_editor_btn.clicked.connect(ActionEditorWindow.toggleWindow)
        hlayout.addWidget(self.action_editor_btn)

        self.checkBtn = QtWidgets.QPushButton(parent)
        self.checkBtn.setText("Validate")
        self.checkBtn.setMaximumWidth(80)
        self.checkBtn.clicked.connect(self.runValidation)
        hlayout.addWidget(self.checkBtn)

        self.buildBtn = QtWidgets.QPushButton(parent)
        self.buildBtn.setText("Build")
        self.buildBtn.setMaximumWidth(80)
        self.buildBtn.clicked.connect(self.runBuild)
        hlayout.addWidget(self.buildBtn)

        self.openBPBtn = QtWidgets.QPushButton(parent)
        self.openBPBtn.setText("Open Blueprint")
        self.openBPBtn.clicked.connect(self.openBlueprintAndReload)
        hlayout.addWidget(self.openBPBtn)

        self.cleanState()

    def rigNameChanged(self, name):
        self.rigNameLabel.setText(self.getRigNameText(name))

    def getRigNameText(self, rigName):
        name = self.blueprintModel.getRigName()
        if not name:
            name = '(unnamed)'
        return name

    def onRigExistsChanged(self):
        self.cleanState()
        self.refreshStateText()
        self.checkBtn.setVisible(not self.rigExists)
        self.buildBtn.setVisible(not self.rigExists)
        self.openBPBtn.setVisible(self.rigExists)

        frameColor = UIColors.RED if self.rigExists else UIColors.BLUE
        frameColor = list(frameColor)
        frameColor[-1] = 40
        self.frame.setStyleSheet(
            ".QFrame#panelFrame{{ {0} }}".format(UIColors.asBGColor(frameColor)))

    def onReadOnlyChanged(self, isReadOnly):
        self.refreshStateText()

    def cleanState(self):
        self.isStateDirty = False
        self.setEnabled(True)  # TODO: True if isBuilding

    def onStateDirty(self):
        if not self.isStateDirty:
            self.isStateDirty = True
            self.setEnabled(False)
            cmds.evalDeferred(self.cleanState)

    def refreshStateText(self):
        stateText = "Rig" if self.rigExists else "Blueprint"
        if self.blueprintModel.isReadOnly():
            stateText += " (read-only)"
        self.rigOrBlueprintLabel.setText(stateText)

    def openBlueprintAndReload(self):
        openFirstRigBlueprint()

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

            # if autoSave:
            self.blueprintModel.save()

            builder = BlueprintBuilder.createBuilderWithCurrentScene(
                blueprint, debug=True)
            builder.showProgressUI = True
            builder.start()

            cmds.evalDeferred(self.onStateDirty)

            # TODO: add build events for situations like this
            cmds.evalDeferred(self.blueprintModel.load, low=True)
