"""
A panel for displaying blueprint attributes and details
"""
import os

import pymel.core as pm

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
        self.blueprintModel.fileChanged.connect(self.onFileChanged)
        self.blueprintModel.readOnlyChanged.connect(self.onReadOnlyChanged)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(self)

        propertiesHeader = createHeaderLabel(parent, "Rig Properties")
        layout.addWidget(propertiesHeader)

        rigNameLabel = QtWidgets.QLabel(parent)
        rigNameLabel.setText("Rig Name")

        self.rigNameText = QtWidgets.QLineEdit(parent)
        self.rigNameText.setText(self.blueprintModel.getRigName())
        self.rigNameText.textChanged.connect(self.rigNameTextChanged)

        formLayout1 = QtWidgets.QFormLayout(parent)
        formLayout1.setWidget(0, QtWidgets.QFormLayout.LabelRole, rigNameLabel)
        formLayout1.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.rigNameText)
        layout.addLayout(formLayout1)

        fileNameLabel = QtWidgets.QLabel(parent)
        fileNameLabel.setText("File Name")

        self.fileNameText = QtWidgets.QLineEdit(parent)
        self.fileNameText.setText(self.getSceneRelativeFilePath(self.blueprintModel.getBlueprintFilepath()))
        self.fileNameText.setReadOnly(True)

        formLayout2 = QtWidgets.QFormLayout(parent)
        formLayout2.setWidget(0, QtWidgets.QFormLayout.LabelRole, fileNameLabel)
        formLayout2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.fileNameText)
        layout.addLayout(formLayout2)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

        self.refreshState()

    def refreshState(self):
        self.rigNameText.setEnabled(not self.blueprintModel.isReadOnly())

    def onRigNameChanged(self, name):
        self.rigNameText.setText(name)

    def onFileChanged(self):
        self.fileNameText.setText(self.getSceneRelativeFilePath(self.blueprintModel.getBlueprintFilepath()))

    def onReadOnlyChanged(self, isReadOnly):
        self.setEnabled(not isReadOnly)

    def rigNameTextChanged(self):
        self.blueprintModel.setRigName(self.rigNameText.text())

    def getSceneRelativeFilePath(self, file_path):
        # get the file name relative to the current scene name
        scene_path = pm.sceneName()
        if scene_path:
            scene_dir = scene_path.dirname()
            rel_path = os.path.relpath(file_path, scene_dir)
            return rel_path

        return file_path
