"""
A panel for displaying blueprint attributes and details
"""

from pulse.vendor.Qt import QtWidgets
from .core import BlueprintUIModel
from .utils import createHeaderLabel



class ManageWidget(QtWidgets.QWidget):
    """
    A panel for displaying blueprint attributes and details
    """

    def __init__(self, parent=None):
        super(ManageWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel

        self.setupUi(self)

        self.blueprintModel.rigNameChanged.connect(self.onRigNameChanged)
        self.blueprintModel.readOnlyChanged.connect(self.onReadOnlyChanged)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(self)

        propertiesHeader = createHeaderLabel(parent, "Rig Properties")
        layout.addWidget(propertiesHeader)

        formLayout1 = QtWidgets.QFormLayout(parent)
        rigNameLabel = QtWidgets.QLabel(parent)
        rigNameLabel.setText("Rig Name")
        self.rigNameText = QtWidgets.QLineEdit(parent)
        self.rigNameText.setText(self.blueprintModel.getRigName())
        self.rigNameText.textChanged.connect(self.rigNameTextChanged)
        formLayout1.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, rigNameLabel)
        formLayout1.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.rigNameText)
        layout.addLayout(formLayout1)

        spacer = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

        self.refreshState()

    def refreshState(self):
        self.rigNameText.setEnabled(not self.blueprintModel.isReadOnly())

    def onRigNameChanged(self, name):
        self.rigNameText.setText(name)

    def onReadOnlyChanged(self, isReadOnly):
        self.setEnabled(not isReadOnly)

    def rigNameTextChanged(self):
        self.blueprintModel.setRigName(self.rigNameText.text())
