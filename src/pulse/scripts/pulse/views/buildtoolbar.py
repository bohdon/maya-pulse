
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm
import pymetanode as meta

import pulse
from .core import PulseWindow
from .actiontree import ActionTreeItemModel


__all__ = [
    'BuildToolbarWidget',
    'BuildToolbarWindow',
]


class BuildToolbarWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(BuildToolbarWidget, self).__init__(parent=parent)

        self.model = ActionTreeItemModel.getSharedModel()
        self.model.modelReset.connect(self.onBlueprintLoaded)

        self.setupUi(self)

    def setupUi(self, parent):
        layout = QtWidgets.QHBoxLayout(parent)

        self.rigNameLabel = QtWidgets.QLabel(parent)
        self.rigNameLabel.setText(self.blueprint.rigName)
        layout.addWidget(self.rigNameLabel)

        checkBtn = QtWidgets.QPushButton(parent)
        checkBtn.setText("Check")
        checkBtn.setMaximumWidth(80)
        checkBtn.clicked.connect(self.runCheck)
        layout.addWidget(checkBtn)

        buildBtn = QtWidgets.QPushButton(parent)
        buildBtn.setText("Build")
        buildBtn.setMaximumWidth(80)
        buildBtn.clicked.connect(self.runBuild)
        layout.addWidget(buildBtn)

    @property
    def blueprint(self):
        return self.model.blueprint

    def onBlueprintLoaded(self):
        self.rigNameLabel.setText(self.blueprint.rigName)

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
