
import logging
import maya.cmds as cmds
import pymel.core as pm

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.core import RigEventsMixin
from .core import PulseWindow
from .core import BlueprintUIModel
from .style import UIColors


__all__ = [
    'BuildToolbarWidget',
]

LOG = logging.getLogger(__name__)


class BuildToolbarWidget(QtWidgets.QWidget, RigEventsMixin):

    def __init__(self, parent=None):
        super(BuildToolbarWidget, self).__init__(parent=parent)

        self.rigExists = len(pulse.getAllRigs()) > 0
        self.isStateDirty = False

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        self.setupUi(self)

        # connect signals
        self.blueprintModel.rigNameChanged.connect(self.rigNameChanged)

    def showEvent(self, event):
        super(BuildToolbarWidget, self).showEvent(event)
        self.onStateDirty()
        self.enableRigEvents()

    def hideEvent(self, event):
        super(BuildToolbarWidget, self).hideEvent(event)
        self.disableRigEvents()

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(4)

        self.frame = QtWidgets.QFrame(parent)
        self.frame.setObjectName("panelFrame")
        layout.addWidget(self.frame)

        hlayout = QtWidgets.QHBoxLayout(self.frame)

        labelLayout = QtWidgets.QVBoxLayout(parent)
        hlayout.addLayout(labelLayout)

        font = QtGui.QFont()
        font.setPointSize(10)
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
        font.setItalic(True)
        self.rigOrBlueprintLabel = QtWidgets.QLabel(parent)
        self.rigOrBlueprintLabel.setFont(font)
        labelLayout.addWidget(self.rigOrBlueprintLabel)

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

    def cleanState(self):
        self.isStateDirty = False
        self.setEnabled(True)
        self.rigExists = len(pulse.getAllRigs()) > 0
        self.checkBtn.setVisible(not self.rigExists)
        self.buildBtn.setVisible(not self.rigExists)
        self.openBPBtn.setVisible(self.rigExists)
        self.rigOrBlueprintLabel.setText(
            "Editing Rig" if self.rigExists else "Editing Blueprint")

        frameColor = UIColors.RED if self.rigExists else UIColors.BLUE
        frameColor = list(frameColor)
        frameColor[-1] = 10
        self.frame.setStyleSheet(
            ".QFrame#panelFrame{{ {0} }}".format(UIColors.asBGColor(frameColor)))

    def onStateDirty(self):
        if not self.isStateDirty:
            self.isStateDirty = True
            self.setEnabled(False)
            cmds.evalDeferred(self.cleanState)

    def onRigCreated(self, node):
        self.rigExists = len(pulse.getAllRigs()) > 0
        self.onStateDirty()

    def onRigDeleted(self, node):
        # node will be deleted, is not yet, so there must be
        # more than one left for any rigs to exist afterwards
        self.rigExists = len(pulse.getAllRigs()) > 1
        self.onStateDirty()

    def openBlueprintAndReload(self):
        pulse.openFirstRigBlueprint()
        self.blueprintModel.loadFromFile()

    def runValidation(self):
        if self.blueprintModel.blueprint is not None:
            pass

    def runBuild(self):
        if self.blueprintModel.blueprint is not None:

            if not pulse.BlueprintBuilder.preBuildValidate(self.blueprintModel.blueprint):
                return

            builder = pulse.BlueprintBuilder.createBuilderWithCurrentScene(
                self.blueprintModel.blueprint, debug=True)
            builder.start()

            cmds.evalDeferred(self.onStateDirty)
