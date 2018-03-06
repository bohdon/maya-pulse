
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm
import pymetanode as meta

import pulse
from .core import PulseWindow
from .style import UIColors
from .actiontree import ActionTreeItemModel


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

        self.rigNameText = QtWidgets.QLineEdit(self)
        self.rigNameText.setText(self.blueprint.rigName)
        self.rigNameText.textChanged.connect(self.rigNameTextChanged)
        layout.addWidget(self.rigNameText)

        createBtn = QtWidgets.QPushButton(self)
        createBtn.setText("Create Default Blueprint")
        createBtn.clicked.connect(pulse.Blueprint.createDefaultBlueprint)
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
        debugOpenBpBtn.clicked.connect(pulse.openFirstRigBlueprint)
        layout.addWidget(debugOpenBpBtn)

        deleteBlueprintBtn = QtWidgets.QPushButton(self)
        deleteBlueprintBtn.setText("Delete Blueprint")
        deleteBlueprintBtn.setStyleSheet(UIColors.asBGColor(UIColors.RED))
        deleteBlueprintBtn.clicked.connect(self.deleteBlueprint)
        layout.addWidget(deleteBlueprintBtn)

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
        pulse.Blueprint.createDefaultBlueprint()
        self.model.reloadBlueprint()
    
    def deleteBlueprint(self):
        pulse.Blueprint.deleteDefaultNode()

    def debugSaveBlueprint(self):
        self.blueprint.saveToDefaultNode()

    def debugPrintSerialized(self):
        import pprint
        blueprint = pulse.Blueprint.fromDefaultNode()
        if blueprint:
            pprint.pprint(blueprint.serialize())



class BlueprintEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseBlueprintEditorWindow'

    def __init__(self, parent=None):
        super(BlueprintEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        widget = BlueprintEditorWidget(self)
        self.setCentralWidget(widget)
