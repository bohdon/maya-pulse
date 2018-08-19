
import logging
import maya.cmds as cmds
import pymel.core as pm

import pulse
from pulse.vendor.Qt import QtWidgets
from pulse.core import RigEventsMixin
from .core import PulseWindow
from .core import BlueprintUIModel


__all__ = [
    'BuildToolbarWidget',
    'BuildToolbarWindow',
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
        self.blueprintModel.blueprintCreated.connect(self.onStateDirty)
        self.blueprintModel.blueprintDeleted.connect(self.onStateDirty)
        self.blueprintModel.rigNameChanged.connect(self.rigNameChanged)

    def showEvent(self, event):
        super(BuildToolbarWidget, self).showEvent(event)
        self.blueprintModel.addSubscriber(self)
        self.enableRigEvents()

    def hideEvent(self, event):
        super(BuildToolbarWidget, self).hideEvent(event)
        self.blueprintModel.removeSubscriber(self)
        self.disableRigEvents()

    def setupUi(self, parent):
        layout = QtWidgets.QHBoxLayout(parent)

        self.rigNameLabel = QtWidgets.QLabel(parent)
        self.rigNameLabel.setText(self.blueprintModel.getRigName())
        layout.addWidget(self.rigNameLabel)

        self.saveBtn = QtWidgets.QPushButton(parent)
        self.saveBtn.setText("Save")
        self.saveBtn.setMaximumWidth(80)
        self.saveBtn.clicked.connect(self.blueprintModel.saveToSceneFile)
        layout.addWidget(self.saveBtn)

        self.loadBtn = QtWidgets.QPushButton(parent)
        self.loadBtn.setText("Load")
        self.loadBtn.setMaximumWidth(80)
        self.loadBtn.clicked.connect(self.blueprintModel.loadFromSceneFile)
        layout.addWidget(self.loadBtn)

        self.createBtn = QtWidgets.QPushButton(parent)
        self.createBtn.setText("Create Blueprint")
        self.createBtn.clicked.connect(self.blueprintModel.createNode)
        layout.addWidget(self.createBtn)

        self.checkBtn = QtWidgets.QPushButton(parent)
        self.checkBtn.setText("Check")
        self.checkBtn.setMaximumWidth(80)
        self.checkBtn.clicked.connect(self.runCheck)
        layout.addWidget(self.checkBtn)

        self.buildBtn = QtWidgets.QPushButton(parent)
        self.buildBtn.setText("Build")
        self.buildBtn.setMaximumWidth(80)
        self.buildBtn.clicked.connect(self.runBuild)
        layout.addWidget(self.buildBtn)

        self.openBPBtn = QtWidgets.QPushButton(parent)
        self.openBPBtn.setText("Open Blueprint")
        self.openBPBtn.clicked.connect(pulse.openFirstRigBlueprint)
        layout.addWidget(self.openBPBtn)

        self.cleanState()

    def rigNameChanged(self, name):
        self.rigNameLabel.setText(self.blueprintModel.getRigName())

    def cleanState(self):
        bpExists = self.blueprintModel.blueprint is not None
        self.isStateDirty = False
        self.setEnabled(True)
        self.createBtn.setVisible(not (bpExists or self.rigExists))
        self.checkBtn.setVisible(bpExists and not self.rigExists)
        self.buildBtn.setVisible(bpExists and not self.rigExists)
        self.openBPBtn.setVisible(self.rigExists)

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

    def runCheck(self):
        if self.blueprintModel.blueprint is not None:
            pass

    def runBuild(self):
        if self.blueprintModel.blueprint is not None:
            # self.model.reloadBlueprint()
            blueprintFile = str(pm.sceneName())
            builder = pulse.BlueprintBuilder(self.blueprintModel.blueprint, blueprintFile=blueprintFile, debug=True)
            builder.start()
            # self.model.reloadBlueprint()


class BuildToolbarWindow(PulseWindow):

    OBJECT_NAME = 'pulseBuildToolbarWindow'

    def __init__(self, parent=None):
        super(BuildToolbarWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        widget = BuildToolbarWidget(self)
        self.setCentralWidget(widget)
