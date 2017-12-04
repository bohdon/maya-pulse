
import pymel.core as pm
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse.joints

from pulse.views.core import buttonCommand
from .core import DesignViewPanel

__all__ = [
    "JointsPanel",
]


class JointsPanel(DesignViewPanel):

    def __init__(self, parent):
        super(JointsPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "Joints"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        gridLayout = QtWidgets.QGridLayout(frame)
        gridLayout.setSpacing(4)

        jointToolBtn = QtWidgets.QPushButton(frame)
        jointToolBtn.setText("Joint Tool")
        jointToolBtn.clicked.connect(buttonCommand(pm.mel.JointTool))
        gridLayout.addWidget(jointToolBtn, 0, 0, 1, 1)

        insertToolBtn = QtWidgets.QPushButton(frame)
        insertToolBtn.setText("Insert Joint Tool")
        insertToolBtn.clicked.connect(buttonCommand(pm.mel.InsertJointTool))
        gridLayout.addWidget(insertToolBtn, 0, 1, 1, 1)

        centerBtn = QtWidgets.QPushButton(frame)
        centerBtn.setText("Center")
        centerBtn.clicked.connect(buttonCommand(pulse.joints.centerSelectedJoints))
        gridLayout.addWidget(centerBtn, 1, 0, 1, 1)

        insertBtn = QtWidgets.QPushButton(frame)
        insertBtn.setText("Insert")
        insertBtn.clicked.connect(buttonCommand(pulse.joints.insertJointForSelected))
        gridLayout.addWidget(insertBtn, 1, 1, 1, 1)

        disableSSCBtn = QtWidgets.QPushButton(frame)
        disableSSCBtn.setText("Disable Scale Compensate")
        disableSSCBtn.clicked.connect(buttonCommand(pulse.joints.disableSegmentScaleCompensateForSelected))
        gridLayout.addWidget(disableSSCBtn, 2, 0, 1, 2)

