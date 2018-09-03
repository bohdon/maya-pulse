
import pulse
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from .core import PulseWindow
from .core import BlueprintUIModel
from .style import UIColors


__all__ = [
    'BlueprintEditorWidget',
    'BlueprintEditorWindow',
]


class BlueprintEditorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(BlueprintEditorWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel

        self.setupUi(self)

        self.blueprintModel.rigNameChanged.connect(self.onRigNameChanged)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(self)

        formLayout1 = QtWidgets.QFormLayout(self)
        rigNameLabel = QtWidgets.QLabel(self)
        rigNameLabel.setText("Rig Name")
        self.rigNameText = QtWidgets.QLineEdit(self)
        self.rigNameText.setText(self.blueprintModel.getRigName())
        self.rigNameText.textChanged.connect(self.rigNameTextChanged)
        formLayout1.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, rigNameLabel)
        formLayout1.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.rigNameText)
        layout.addLayout(formLayout1)

        initBtn = QtWidgets.QPushButton(self)
        initBtn.setText("Initialize Blueprint")
        initBtn.clicked.connect(self.initBlueprint)
        layout.addWidget(initBtn)

        debugPrintBtn = QtWidgets.QPushButton(self)
        debugPrintBtn.setText("Debug Print YAML")
        debugPrintBtn.clicked.connect(self.debugPrintSerialized)
        layout.addWidget(debugPrintBtn)

        spacer = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

        self.refreshState()

    def refreshState(self):
        self.rigNameText.setEnabled(not self.blueprintModel.isReadOnly())

    def onRigNameChanged(self, name):
        self.rigNameText.setText(name)

    def rigNameTextChanged(self):
        self.blueprintModel.setRigName(self.rigNameText.text())

    def initBlueprint(self):
        self.blueprintModel.initializeBlueprint()

    def debugPrintSerialized(self):
        print(self.blueprintModel.blueprint.dumpYaml())


class BlueprintEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseBlueprintEditorWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.blueprinteditor'

    def __init__(self, parent=None):
        super(BlueprintEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        widget = BlueprintEditorWidget(self)
        layout.addWidget(widget)
