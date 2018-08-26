
from functools import partial
import pymel.core as pm
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.vendor.Qt.QtWidgets import QPushButton

from pulse.prefs import optionVarProperty
from pulse.views.utils import getIcon
from pulse.views.utils import undoAndRepeatPartial as cmd
from pulse.views.style import UIColors
from pulse import editorutils
from .core import DesignViewPanel

__all__ = [
    "JointOrientsPanel",
    "JointsPanel",
]


class JointsPanel(DesignViewPanel):

    def getPanelDisplayName(self):
        return "Joints"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        self.setupButtonGridUi(frame)

    def setupButtonGridUi(self, parent):
        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        jointToolBtn = QPushButton(parent)
        jointToolBtn.setText("Joint Tool")
        jointToolBtn.clicked.connect(cmd(pm.mel.JointTool))
        gridLayout.addWidget(jointToolBtn, 0, 0, 1, 1)

        insertToolBtn = QPushButton(parent)
        insertToolBtn.setText("Insert Joint Tool")
        insertToolBtn.clicked.connect(cmd(pm.mel.InsertJointTool))
        gridLayout.addWidget(insertToolBtn, 0, 1, 1, 1)

        centerBtn = QPushButton(parent)
        centerBtn.setText("Center")
        centerBtn.clicked.connect(cmd(editorutils.centerSelectedJoints))
        gridLayout.addWidget(centerBtn, 1, 0, 1, 1)

        insertBtn = QPushButton(parent)
        insertBtn.setText("Insert")
        insertBtn.clicked.connect(cmd(editorutils.insertJointForSelected))
        gridLayout.addWidget(insertBtn, 1, 1, 1, 1)

        disableSSCBtn = QPushButton(parent)
        disableSSCBtn.setText("Disable Scale Compensate")
        disableSSCBtn.clicked.connect(
            cmd(editorutils.disableSegmentScaleCompensateForSelected))
        gridLayout.addWidget(disableSSCBtn, 2, 0, 1, 2)


class JointOrientsPanel(DesignViewPanel):
    """
    Util widget for orienting joints.
    """

    AXIS_ORDER_OPTIONS = ['XYZ', 'YZX', 'ZXY', 'XZY', 'YXZ', 'ZYX']
    UP_AXIS_OPTIONS = ['X', 'Y', 'Z']

    orientAxisOrder = optionVarProperty('pulse.editor.orientAxisOrder', 0)
    orientUpAxis = optionVarProperty('pulse.editor.orientUpAxis', 1)
    syncJointAxes = optionVarProperty('pulse.editor.syncJointAxes', True)
    orientPreserveChildren = optionVarProperty(
        'pulse.editor.orientPreserveChildren', True)
    orientPreserveShapes = optionVarProperty(
        'pulse.editor.orientPreserveShapes', True)

    def setOrientAxisOrder(self, value):
        self.orientAxisOrder = value

    def setOrientUpAxis(self, value):
        self.orientUpAxis = value

    def setSyncJointAxes(self, value):
        self.syncJointAxes = value

    def setOrientPreserveChildren(self, value):
        self.orientPreserveChildren = value

    def setOrientPreserveShapes(self, value):
        self.orientPreserveShapes = value

    def getPanelDisplayName(self):
        return "Joint Orients"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        self.setupContenUi(frame)

    def setupContenUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        # button grid
        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)
        layout.addLayout(gridLayout)

        toggleCBBtn = QPushButton(parent)
        toggleCBBtn.setText('Toggle Channel Box Attrs')
        toggleCBBtn.setStatusTip(
            "Toggle the display of rotateAxis, localPivot, and other "
            "attributes in the channel box")
        toggleCBBtn.clicked.connect(
            cmd(editorutils.toggleDetailedChannelBoxForSelected))
        gridLayout.addWidget(toggleCBBtn, 0, 0, 1, 1)

        toggleLRABtn = QPushButton(parent)
        toggleLRABtn.setText('Toggle LRAs')
        toggleLRABtn.setStatusTip(
            "Toggle the display of local rotation axes")
        toggleLRABtn.clicked.connect(
            cmd(editorutils.toggleLocalRotationAxesForSelected))
        gridLayout.addWidget(toggleLRABtn, 0, 1, 1, 1)

        # orient rotation buttons
        self.keepChildPosCheck = QtWidgets.QCheckBox(parent)
        self.keepChildPosCheck.setText("Preserve Children")
        self.keepChildPosCheck.setStatusTip(
            "Preseve the positions of child nodes when rotating "
            "or orienting a transform or joint")
        self.keepChildPosCheck.setChecked(self.orientPreserveChildren)
        self.keepChildPosCheck.stateChanged.connect(
            self.setOrientPreserveChildren)
        layout.addWidget(self.keepChildPosCheck)

        self.keepShapeCheck = QtWidgets.QCheckBox(parent)
        self.keepShapeCheck.setText("Preserve Shapes")
        self.keepShapeCheck.setStatusTip(
            "Preseve the orientation of shapes when rotating nodes")
        self.keepShapeCheck.setChecked(self.orientPreserveShapes)
        self.keepShapeCheck.stateChanged.connect(self.setOrientPreserveShapes)
        layout.addWidget(self.keepShapeCheck)

        # sync axes checkbox
        self.syncJointAxesCheck = QtWidgets.QCheckBox(parent)
        self.syncJointAxesCheck.setText('Keep Translate and Rotate Synced')
        self.syncJointAxesCheck.setStatusTip(
            "When enabled, joint translate and scale axes are automatically "
            "updated when the jointOrient and rotateAxis values are changed.")
        self.syncJointAxesCheck.setChecked(self.syncJointAxes)
        self.syncJointAxesCheck.stateChanged.connect(self.setSyncJointAxes)
        layout.addWidget(self.syncJointAxesCheck)

        # sync axes button
        syncAxesBtn = QtWidgets.QPushButton(parent)
        syncAxesBtn.setText("Sync Axes")
        syncAxesBtn.setStatusTip(
            "Match the translate and scale axes of a "
            "joint to its orientation")
        syncAxesBtn.clicked.connect(self.matchJointRotationToOrientForSelected)
        layout.addWidget(syncAxesBtn)

        rotateForm = self.createRotateAxisForm(parent)
        layout.addWidget(rotateForm)

        # axis settings
        axisLayout = QtWidgets.QHBoxLayout(parent)
        axisLayout.setSpacing(8)

        # joint up axis
        comboLayout1 = QtWidgets.QFormLayout(parent)
        comboLayout1.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.ExpandingFieldsGrow)
        axisLayout.addLayout(comboLayout1)

        upAxisLabel = QtWidgets.QLabel(parent)
        upAxisLabel.setText("Up Axis")
        comboLayout1.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, upAxisLabel)

        self.upAxisCombo = QtWidgets.QComboBox(parent)
        for option in self.UP_AXIS_OPTIONS:
            self.upAxisCombo.addItem(option)
        self.upAxisCombo.setCurrentIndex(self.orientUpAxis)
        self.upAxisCombo.currentIndexChanged.connect(self.setOrientUpAxis)
        comboLayout1.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.upAxisCombo)

        # joint orient order
        comboLayout2 = QtWidgets.QFormLayout(parent)
        comboLayout2.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.ExpandingFieldsGrow)
        axisLayout.addLayout(comboLayout2)

        axisOrderLabel = QtWidgets.QLabel(parent)
        axisOrderLabel.setText("Axis Order")
        comboLayout2.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, axisOrderLabel)

        self.axisOrderCombo = QtWidgets.QComboBox(parent)
        for option in self.AXIS_ORDER_OPTIONS:
            self.axisOrderCombo.addItem(option)
        self.axisOrderCombo.setCurrentIndex(self.orientAxisOrder)
        self.axisOrderCombo.currentIndexChanged.connect(
            self.setOrientAxisOrder)
        comboLayout2.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.axisOrderCombo)

        # include children check
        formLayout3 = QtWidgets.QFormLayout(parent)
        formLayout3.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.ExpandingFieldsGrow)
        axisLayout.addLayout(formLayout3)

        axisOrderLabel = QtWidgets.QLabel(parent)
        axisOrderLabel.setText("Include Children")
        formLayout3.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, axisOrderLabel)

        self.includeChildrenCheck = QtWidgets.QCheckBox(parent)
        formLayout3.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.includeChildrenCheck)

        layout.addLayout(axisLayout)

        # orient buttons
        hboxLayout2 = QtWidgets.QHBoxLayout(parent)
        hboxLayout2.setSpacing(2)

        # orient to world button
        orientToWorldBtn = QtWidgets.QPushButton(parent)
        orientToWorldBtn.setText("Orient to World")
        orientToWorldBtn.clicked.connect(self.orientToWorldForSelected)
        hboxLayout2.addWidget(orientToWorldBtn)

        # orient to world button
        orientToJointBtn = QtWidgets.QPushButton(parent)
        orientToJointBtn.setText("Orient to Joint")
        orientToJointBtn.clicked.connect(self.orientToJointForSelected)
        hboxLayout2.addWidget(orientToJointBtn)

        layout.addLayout(hboxLayout2)

    def createRotateAxisForm(self, parent):
        widget = QtWidgets.QWidget(parent)

        layout = QtWidgets.QHBoxLayout(parent)
        layout.setMargin(0)
        layout.setSpacing(2)
        widget.setLayout(layout)

        def createRotateOrientsButton(text, color, axis, degrees):
            _axes = {0: 'X', 1: 'Y', 2: 'Z'}

            btn = QtWidgets.QPushButton(parent)
            btn.setText(text)
            btn.setStatusTip(
                "Rotate the components of the selected controls "
                "{0} degrees around the {1} axis".format(degrees, _axes[axis]))
            btn.setStyleSheet(UIColors.asBGColor(color))
            btn.clicked.connect(
                partial(self.rotateSelectedOrientsAroundAxis, axis, degrees))
            return btn

        btn = createRotateOrientsButton('- X', UIColors.RED, 0, -90)
        layout.addWidget(btn)
        btn = createRotateOrientsButton('+ X', UIColors.RED, 0, 90)
        layout.addWidget(btn)
        btn = createRotateOrientsButton('- Y', UIColors.GREEN, 1, -90)
        layout.addWidget(btn)
        btn = createRotateOrientsButton('+ Y', UIColors.GREEN, 1, 90)
        layout.addWidget(btn)
        btn = createRotateOrientsButton('- Z', UIColors.BLUE, 2, -90)
        layout.addWidget(btn)
        btn = createRotateOrientsButton('+ Z', UIColors.BLUE, 2, 90)
        layout.addWidget(btn)

        return widget

    def getOrientUpAxisStr(self):
        """
        Returns:
            An int representing the up axis.
                0 = X, 1 = Y, 2 = Z
        """
        return self.UP_AXIS_OPTIONS[self.orientUpAxis]

    def getOrientAxisOrderStr(self):
        """
        Returns:
            A string representing the orient axis order,
            e.g. 'XYZ', 'ZYX', ...
        """
        return self.AXIS_ORDER_OPTIONS[self.orientAxisOrder]

    def rotateSelectedOrientsAroundAxis(self, axis, degrees):
        func = cmd(editorutils.rotateSelectedOrientsAroundAxis, axis, degrees)
        func()

    def orientToWorldForSelected(self):
        func = cmd(editorutils.orientToWorldForSelected)
        func()

    def orientToJointForSelected(self):
        func = cmd(editorutils.orientToJointForSelected)
        func()

    def matchJointRotationToOrientForSelected(self):
        func = cmd(editorutils.matchJointRotationToOrientForSelected)
        func()
