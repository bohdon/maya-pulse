
from Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm
import pymetanode as meta

import pulse
from pulse.views.core import PulseWindow
from pulse.views.actiontree import ActionTreeItemModel


__all__ = [
    'BlueprintEditorWidget',
    'BlueprintEditorWindow',
]


class BlueprintEditorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(BlueprintEditorWidget, self).__init__(parent=parent)

        self.model = ActionTreeItemModel.getSharedModel()
        self.model.modelReset.connect(self.onBlueprintLoaded)

        layout = QtWidgets.QVBoxLayout(self)

        buildBtn = QtWidgets.QPushButton(self)
        buildBtn.setText("Build Rig")
        buildBtn.clicked.connect(self.buildRig)
        layout.addWidget(buildBtn)

        self.rigNameText = QtWidgets.QLineEdit(self)
        self.rigNameText.setText(self.blueprint.rigName)
        self.rigNameText.textChanged.connect(self.rigNameTextChanged)
        layout.addWidget(self.rigNameText)

        createBtn = QtWidgets.QPushButton(self)
        createBtn.setText("Create Default Blueprint")
        createBtn.clicked.connect(self.createDefaultBlueprint)
        layout.addWidget(createBtn)

        saveBtn = QtWidgets.QPushButton(self)
        saveBtn.setText("Debug Save Blueprint")
        saveBtn.clicked.connect(self.debugSaveBlueprint)
        layout.addWidget(saveBtn)

        debugPrintBtn = QtWidgets.QPushButton(self)
        debugPrintBtn.setText("Debug Print Serialized")
        debugPrintBtn.clicked.connect(self.debugPrintSerialized)
        layout.addWidget(debugPrintBtn)

        debugOpenBpBtn = QtWidgets.QPushButton(self)
        debugOpenBpBtn.setText("Debug Open Blueprint Scene")
        debugOpenBpBtn.clicked.connect(self.debugOpenBlueprintScene)
        layout.addWidget(debugOpenBpBtn)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

    @property
    def blueprint(self):
        return self.model.blueprint

    def onBlueprintLoaded(self):
        self.rigNameText.setText(self.blueprint.rigName)

    def rigNameTextChanged(self):
        self.blueprint.rigName = self.rigNameText.text()
        self.blueprint.saveToDefaultNode()

    def createDefaultBlueprint(self):
        blueprint = pulse.Blueprint()
        blueprint.initializeDefaultActions()
        blueprint.saveToDefaultNode()
        self.model.reloadBlueprint()

    def buildRig(self):
        self.model.reloadBlueprint()
        blueprintFile = str(pm.sceneName())
        builder = pulse.BlueprintBuilder(self.blueprint, blueprintFile=blueprintFile, debug=True)
        builder.start()

    def debugSaveBlueprint(self):
        self.blueprint.saveToDefaultNode()

    def debugPrintSerialized(self):
        import pprint
        blueprint = pulse.Blueprint.fromDefaultNode()
        if blueprint:
            pprint.pprint(blueprint.serialize())

    def debugOpenBlueprintScene(self):
        rigs = pulse.getAllRigs()
        if not rigs:
            print('No rig in the scene')
            return

        rigdata = meta.getMetaData(rigs[0], pulse.RIG_METACLASS)
        blueprintFile = rigdata.get('blueprintFile')
        if not blueprintFile:
            print('No blueprintFile set on the rig')
            return

        print('Opening blueprint: ' + blueprintFile)
        pm.openFile(blueprintFile, f=True)



class BlueprintEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseBlueprintEditorWindow'

    def __init__(self, parent=None):
        super(BlueprintEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        widget = BlueprintEditorWidget(self)
        self.setCentralWidget(widget)
