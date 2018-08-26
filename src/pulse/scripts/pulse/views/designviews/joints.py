
import pymel.core as pm
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.vendor.Qt.QtWidgets import QPushButton

import pulse.joints

from pulse.views.utils import getIcon
from pulse.views.utils import undoAndRepeatPartial as cmd
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
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        jointToolBtn = QPushButton(frame)
        jointToolBtn.setText("Joint Tool")
        jointToolBtn.clicked.connect(cmd(pm.mel.JointTool))
        gridLayout.addWidget(jointToolBtn, 0, 0, 1, 1)

        insertToolBtn = QPushButton(frame)
        insertToolBtn.setText("Insert Joint Tool")
        insertToolBtn.clicked.connect(cmd(pm.mel.InsertJointTool))
        gridLayout.addWidget(insertToolBtn, 0, 1, 1, 1)

        centerBtn = QPushButton(frame)
        centerBtn.setText("Center")
        centerBtn.clicked.connect(cmd(pulse.joints.centerSelectedJoints))
        gridLayout.addWidget(centerBtn, 1, 0, 1, 1)

        insertBtn = QPushButton(frame)
        insertBtn.setText("Insert")
        insertBtn.clicked.connect(cmd(pulse.joints.insertJointForSelected))
        gridLayout.addWidget(insertBtn, 1, 1, 1, 1)

        disableSSCBtn = QPushButton(frame)
        disableSSCBtn.setText("Disable Scale Compensate")
        disableSSCBtn.clicked.connect(
            cmd(pulse.joints.disableSegmentScaleCompensateForSelected))
        gridLayout.addWidget(disableSSCBtn, 2, 0, 1, 2)

