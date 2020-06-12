
from functools import partial
import pymel.core as pm
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.vendor.Qt.QtWidgets import QPushButton

from pulse.prefs import optionVarProperty
from pulse.views import utils as viewutils
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

        insertToolBtn = QPushButton(parent)
        insertToolBtn.setText("Insert Joint Tool")
        insertToolBtn.clicked.connect(cmd(pm.mel.InsertJointTool))

        centerBtn = QPushButton(parent)
        centerBtn.setText("Center")
        centerBtn.clicked.connect(cmd(editorutils.centerSelectedJoints))

        insertBtn = QPushButton(parent)
        insertBtn.setText("Insert")
        insertBtn.clicked.connect(cmd(editorutils.insertJointForSelected))

        disableSSCBtn = QPushButton(parent)
        disableSSCBtn.setText("Disable Scale Compensate")
        disableSSCBtn.clicked.connect(
            cmd(editorutils.disableSegmentScaleCompensateForSelected))

        gridItems = [
            [jointToolBtn, insertToolBtn],
            [centerBtn, insertBtn],
            [disableSSCBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)


class JointOrientsPanel(DesignViewPanel):
    """
    Util widget for orienting joints.
    """

    AXIS_ORDER_OPTIONS = ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX']
    UP_AXIS_OPTIONS = ['X', 'Y', 'Z']

    orientAxisOrder = optionVarProperty('pulse.editor.orientAxisOrder', 0)
    orientUpAxis = optionVarProperty('pulse.editor.orientUpAxis', 1)
    syncJointAxes = optionVarProperty('pulse.editor.syncJointAxes', True)
    orientPreserveChildren = optionVarProperty(
        'pulse.editor.orientPreserveChildren', True)
    orientPreserveShapes = optionVarProperty(
        'pulse.editor.orientPreserveShapes', True)
    orientIncludeChildren = optionVarProperty(
        'pulse.editor.orientIncludeChildren', True)

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

    def setOrientIncludeChildren(self, value):
        self.orientIncludeChildren = value

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

        # settings
        # --------
        self.keepChildPosCheck = QtWidgets.QCheckBox(parent)
        self.keepChildPosCheck.setText("Preserve Children")
        self.keepChildPosCheck.setStatusTip(
            "Preseve the positions of child nodes when rotating "
            "or orienting a transform or joint")
        self.keepChildPosCheck.setChecked(self.orientPreserveChildren)
        self.keepChildPosCheck.stateChanged.connect(
            self.setOrientPreserveChildren)

        self.keepShapeCheck = QtWidgets.QCheckBox(parent)
        self.keepShapeCheck.setText("Preserve Shapes")
        self.keepShapeCheck.setStatusTip(
            "Preseve the orientation of shapes when rotating nodes")
        self.keepShapeCheck.setChecked(self.orientPreserveShapes)
        self.keepShapeCheck.stateChanged.connect(self.setOrientPreserveShapes)

        self.syncJointAxesCheck = QtWidgets.QCheckBox(parent)
        self.syncJointAxesCheck.setText('Keep Axes Synced')
        self.syncJointAxesCheck.setStatusTip(
            "When enabled, joint translate and scale axes are automatically "
            "updated when the jointOrient and rotateAxis values are changed.")
        self.syncJointAxesCheck.setChecked(self.syncJointAxes)
        self.syncJointAxesCheck.stateChanged.connect(self.setSyncJointAxes)

        self.includeChildrenCheck = QtWidgets.QCheckBox(parent)
        self.includeChildrenCheck.setText("Include All Children")
        self.includeChildrenCheck.setStatusTip(
            "Update all child joints when using orient to joint or world")
        self.includeChildrenCheck.setChecked(self.orientIncludeChildren)
        self.includeChildrenCheck.stateChanged.connect(
            self.setOrientIncludeChildren)

        # joint orient axes
        hlayout = QtWidgets.QHBoxLayout(parent)
        hlayout.setSpacing(4)

        axisOrderLabel = QtWidgets.QLabel(parent)
        axisOrderLabel.setText("Orient Axes")

        self.axisOrderCombo = QtWidgets.QComboBox(parent)
        for option in self.AXIS_ORDER_OPTIONS:
            optionStr = '{0} forward, {1} up'.format(option[0], option[1])
            self.axisOrderCombo.addItem(optionStr)
        self.axisOrderCombo.setCurrentIndex(self.orientAxisOrder)
        self.axisOrderCombo.setStatusTip(
            "The local axes to use for forward / up / secondary")
        self.axisOrderCombo.currentIndexChanged.connect(
            self.setOrientAxisOrder)

        self.upAxisCombo = QtWidgets.QComboBox(parent)
        for option in self.UP_AXIS_OPTIONS:
            optionStr = '{0} world up'.format(option)
            self.upAxisCombo.addItem(optionStr)
        self.upAxisCombo.setCurrentIndex(self.orientUpAxis)
        self.upAxisCombo.setStatusTip(
            "The world axis that up vector of the joint should point towards")
        self.upAxisCombo.currentIndexChanged.connect(self.setOrientUpAxis)

        hlayout.addWidget(axisOrderLabel)
        hlayout.addWidget(self.axisOrderCombo)
        hlayout.addWidget(self.upAxisCombo)
        hlayout.addItem(viewutils.createHSpacer())

        layout.addWidget(self.keepChildPosCheck)
        layout.addWidget(self.keepShapeCheck)
        layout.addWidget(self.syncJointAxesCheck)
        layout.addWidget(self.includeChildrenCheck)
        layout.addLayout(hlayout)

        # button grid
        # -----------
        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        toggleCBBtn = QPushButton(parent)
        toggleCBBtn.setText('Toggle Channel Box Attrs')
        toggleCBBtn.setStatusTip(
            "Toggle the display of rotateAxis, localPivot, and other "
            "attributes in the channel box")
        toggleCBBtn.clicked.connect(
            cmd(editorutils.toggleDetailedChannelBoxForSelected))

        toggleLRABtn = QPushButton(parent)
        toggleLRABtn.setText('Toggle LRAs')
        toggleLRABtn.setStatusTip(
            "Toggle the display of local rotation axes")
        toggleLRABtn.clicked.connect(
            cmd(self.toggleLocalRotationAxesForSelected))

        fixupOrientBtn = QtWidgets.QPushButton(parent)
        fixupOrientBtn.setText("Fixup Orient")
        fixupOrientBtn.setStatusTip(
            "Adjust joint orientation to point down the bone, whilst preserving "
            "the other axes as much as possible. "
            "Currently hard-coded to point down X and prioritize Z")
        fixupOrientBtn.clicked.connect(
            self.fixupJointOrientForSelected)

        syncAxesBtn = QtWidgets.QPushButton(parent)
        syncAxesBtn.setText("Sync Axes")
        syncAxesBtn.setStatusTip(
            "Match the translate and scale axes of a "
            "joint to its orientation")
        syncAxesBtn.clicked.connect(self.matchJointRotationToOrientForSelected)

        orientToJointBtn = QtWidgets.QPushButton(parent)
        orientToJointBtn.setText("Orient to Joint")
        orientToJointBtn.clicked.connect(self.orientToJointForSelected)

        orientToWorldBtn = QtWidgets.QPushButton(parent)
        orientToWorldBtn.setText("Orient to World")
        orientToWorldBtn.clicked.connect(self.orientToWorldForSelected)

        interactiveOrientBtn = QtWidgets.QPushButton(parent)
        interactiveOrientBtn.setText("Interactive Orient")
        interactiveOrientBtn.clicked.connect(self.interactiveOrientForSelected)

        orientIKJointsBtn = QtWidgets.QPushButton(parent)
        orientIKJointsBtn.setText("Orient IK Joints")
        orientIKJointsBtn.clicked.connect(self.orientIKJointsForSelected)

        gridItems = [
            [orientToJointBtn, orientToWorldBtn],
            [fixupOrientBtn, syncAxesBtn],
            [toggleCBBtn, toggleLRABtn],
            [interactiveOrientBtn, orientIKJointsBtn]
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)
        layout.addLayout(gridLayout)

        # rotate orient buttons
        # ---------------------
        rotateForm = self.createRotateAxisForm(parent)
        layout.addWidget(rotateForm)

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
            An str representing the up axis
                e.g. 'x', 'y', 'z'
        """
        return self.UP_AXIS_OPTIONS[self.orientUpAxis].lower()

    def getOrientAxisOrderStr(self):
        """
        Returns:
            A string representing the orient axis order,
                e.g. 'xyz', 'zyx', ...
        """
        return self.AXIS_ORDER_OPTIONS[self.orientAxisOrder].lower()

    def toggleLocalRotationAxesForSelected(self):
        kw = dict(
            includeChildren=self.orientIncludeChildren,
        )
        cmd(editorutils.toggleLocalRotationAxesForSelected, **kw)()

    def rotateSelectedOrientsAroundAxis(self, axis, degrees):
        kw = dict(
            preserveChildren=self.orientPreserveChildren,
            preserveShapes=self.orientPreserveShapes,
            syncJointAxes=self.syncJointAxes,
        )
        cmd(editorutils.rotateSelectedOrientsAroundAxis,
            axis, degrees, **kw)()

    def interactiveOrientForSelected(self):
        cmd(editorutils.interactiveOrientForSelected)()

    def orientToWorldForSelected(self):
        kw = dict(
            includeChildren=self.orientIncludeChildren,
            preserveChildren=self.orientPreserveChildren,
            preserveShapes=self.orientPreserveShapes,
            syncJointAxes=self.syncJointAxes,
        )
        cmd(editorutils.orientToWorldForSelected, **kw)()

    def orientToJointForSelected(self):
        kw = dict(
            axisOrder=self.getOrientAxisOrderStr(),
            upAxisStr=self.getOrientUpAxisStr(),
            includeChildren=self.orientIncludeChildren,
            preserveChildren=self.orientPreserveChildren,
            preserveShapes=self.orientPreserveShapes,
            syncJointAxes=self.syncJointAxes,
        )
        cmd(editorutils.orientToJointForSelected, **kw)()

    def orientIKJointsForSelected(self):
        kw = dict(
            aimAxis=self.getOrientAxisOrderStr()[0],
            poleAxis=self.getOrientUpAxisStr(),
            preserveChildren=self.orientPreserveChildren,
        )
        cmd(editorutils.orientIKJointsForSelected, **kw)()

    def fixupJointOrientForSelected(self):
        kw = dict(
            aimAxis=self.getOrientAxisOrderStr()[0],
            keepAxis=self.getOrientUpAxisStr(),
            preserveChildren=self.orientPreserveChildren,
        )
        cmd(editorutils.fixupJointOrientForSelected, **kw)()

    def matchJointRotationToOrientForSelected(self):
        kw = dict(
            preserveChildren=self.orientPreserveChildren,
        )
        cmd(editorutils.matchJointRotationToOrientForSelected, **kw)()
