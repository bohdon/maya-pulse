
from Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm
import pymetanode as meta

import pulse
from pulse.views.core import PulseWindow
from pulse.views.actiontree import ActionTreeItemModel


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

        rigNameLabel = QtWidgets.QLabel(parent)
        layout.addWidget(rigNameLabel)

        checkBtn = QtWidgets.QPushButton(parent)
        layout.addWidget(checkBtn)

        buildBtn = QtWidgets.QPushButton(parent)
        layout.addWidget(buildBtn)

    @property
    def blueprint(self):
        return self.model.blueprint

    def onBlueprintLoaded(self):
        # self.rigNameText.setText(self.blueprint.rigName)
        pass

    def runCheck(self):
        pass

    def runBuild(self):
        pass
        # self.model.reloadBlueprint()
        # blueprintFile = str(pm.sceneName())
        # builder = pulse.BlueprintBuilder(self.blueprint, blueprintFile=blueprintFile, debug=True)
        # builder.start()
        # self.model.reloadBlueprint()


class BuildToolbarWindow(PulseWindow):

    OBJECT_NAME = 'pulseBuildToolbarWindow'

    def __init__(self, parent=None):
        super(BuildToolbarWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        widget = BuildToolbarWidget(self)
        self.setCentralWidget(widget)
