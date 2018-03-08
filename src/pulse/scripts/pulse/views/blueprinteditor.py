
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm
import pymetanode as meta

import pulse
from .core import PulseWindow
from .core import BlueprintUIModel, BuildItemTreeModel
from .style import UIColors


__all__ = [
    'BlueprintEditorWidget',
    'BlueprintEditorWindow',
]


class BlueprintEditorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(BlueprintEditorWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildItemTreeModel

        layout = QtWidgets.QVBoxLayout(self)

        self.rigNameText = QtWidgets.QLineEdit(self)
        self.rigNameText.setText(self.blueprintModel.getRigName())
        self.rigNameText.textChanged.connect(self.rigNameTextChanged)
        layout.addWidget(self.rigNameText)

        createBtn = QtWidgets.QPushButton(self)
        createBtn.setText("Create Default Blueprint")
        createBtn.clicked.connect(pulse.Blueprint.createDefaultBlueprint)
        layout.addWidget(createBtn)

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

    def rigNameTextChanged(self):
        self.blueprintModel.setRigName(self.rigNameText.text())

    def createDefaultBlueprint(self):
        pulse.Blueprint.createDefaultBlueprint()
    
    def deleteBlueprint(self):
        pulse.Blueprint.deleteDefaultNode()

    def debugPrintSerialized(self):
        import pprint
        if self.blueprintModel.blueprint:
            pprint.pprint(self.blueprintModel.blueprint.serialize())
        else:
            print('No Blueprint')



class BlueprintEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseBlueprintEditorWindow'

    def __init__(self, parent=None):
        super(BlueprintEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        widget = BlueprintEditorWidget(self)
        self.setCentralWidget(widget)
