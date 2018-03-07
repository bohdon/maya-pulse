
import logging
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import maya.cmds as cmds
import maya.OpenMaya as om
import pymel.core as pm
import pymetanode as meta

import pulse
import pulse.events
from .core import PulseWindow
from .actiontree import ActionTreeItemModel


__all__ = [
    'BuildToolbarWidget',
    'BuildToolbarWindow',
]

LOG = logging.getLogger('pulse.views.buildtoolbar')
LOG.level = logging.INFO


class BuildToolbarWidget(QtWidgets.QWidget, pulse.events.BlueprintEventsMixin, pulse.events.RigEventsMixin):

    def __init__(self, parent=None):
        super(BuildToolbarWidget, self).__init__(parent=parent)

        # TODO: simplify overall ui functionality for visible-based
        #   state changes and events that can be reused for other widgets

        self.enableBlueprintChangeEvents(pulse.BLUEPRINT_NODENAME)
        self.blueprintExists = pulse.Blueprint.doesDefaultNodeExist()
        self.rigExists = len(pulse.getAllRigs()) > 0
        self.isStateDirty = False

        self.model = ActionTreeItemModel.getSharedModel()
        self.model.modelReset.connect(self.onBlueprintLoaded)

        self.setupUi(self)

    def showEvent(self, event):
        super(BuildToolbarWidget, self).showEvent(event)
        self.enableBlueprintEvents()
        self.enableRigEvents()

    def hideEvent(self, event):
        super(BuildToolbarWidget, self).hideEvent(event)
        self.disableBlueprintEvents()
        self.disableRigEvents()

    def setupUi(self, parent):
        layout = QtWidgets.QHBoxLayout(parent)

        self.rigNameLabel = QtWidgets.QLabel(parent)
        self.rigNameLabel.setText(self.blueprint.rigName)
        layout.addWidget(self.rigNameLabel)

        self.createBtn = QtWidgets.QPushButton(parent)
        self.createBtn.setText("Create Blueprint")
        self.createBtn.clicked.connect(self.createBlueprint)
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

        self.onPulseNodesChanged()

    def onPulseNodesChanged(self):
        self.isStateDirty = False
        self.setEnabled(True)
        self.createBtn.setVisible(not (self.blueprintExists or self.rigExists))
        self.checkBtn.setVisible(self.blueprintExists and not self.rigExists)
        self.buildBtn.setVisible(self.blueprintExists and not self.rigExists)
        self.openBPBtn.setVisible(self.rigExists)
    
    def onStateDirty(self):
        if not self.isStateDirty:
            self.isStateDirty = True
            self.setEnabled(False)
            cmds.evalDeferred(self.onPulseNodesChanged)

    def onBlueprintCreated(self, node):
        self.blueprintExists = True
        self.onStateDirty()

    def onBlueprintDeleted(self, node):
        if node.nodeName() == pulse.BLUEPRINT_NODENAME:
            self.blueprintExists = False
            self.onStateDirty()

    def onRigCreated(self, node):
        self.rigExists = len(pulse.getAllRigs()) > 0
        self.onStateDirty()

    def onRigDeleted(self, node):
        # node will be deleted, is not yet, so there must be
        # more than one left for any rigs to exist afterwards
        self.rigExists = len(pulse.getAllRigs()) > 1
        self.onStateDirty()

    @property
    def blueprint(self):
        return self.model.blueprint

    def onBlueprintLoaded(self):
        self.rigNameLabel.setText(self.blueprint.rigName)

    def createBlueprint(self):
        pulse.Blueprint.createDefaultBlueprint()
        self.model.reloadBlueprint()

    def runCheck(self):
        pass

    def runBuild(self):
        self.model.reloadBlueprint()
        blueprintFile = str(pm.sceneName())
        builder = pulse.BlueprintBuilder(self.blueprint, blueprintFile=blueprintFile, debug=True)
        builder.start()
        self.model.reloadBlueprint()


class BuildToolbarWindow(PulseWindow):

    OBJECT_NAME = 'pulseBuildToolbarWindow'

    def __init__(self, parent=None):
        super(BuildToolbarWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        widget = BuildToolbarWidget(self)
        self.setCentralWidget(widget)
