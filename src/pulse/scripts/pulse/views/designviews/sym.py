
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm

import pulse.nodes
import pulse.sym

from pulse.prefs import optionVarProperty
from pulse.views import utils as viewutils
from pulse.views.utils import undoAndRepeatPartial as cmd
from pulse import editorutils
from .core import DesignViewPanel

__all__ = [
    "SymmetryPanel",
]


class SymmetryPanel(DesignViewPanel):

    mirrorRecursive = optionVarProperty(
        'pulse.editor.mirrorRecursive', True)
    mirrorTransforms = optionVarProperty(
        'pulse.editor.mirrorTransforms', True)
    mirrorParenting = optionVarProperty(
        'pulse.editor.mirrorParenting', True)
    mirrorAppearance = optionVarProperty(
        'pulse.editor.mirrorAppearance', True)
    mirrorAllowCreate = optionVarProperty(
        'pulse.editor.mirrorAllowCreate', True)

    def setMirrorRecursive(self, value):
        self.mirrorRecursive = value

    def setMirrorTransforms(self, value):
        self.mirrorTransforms = value

    def setMirrorParenting(self, value):
        self.mirrorParenting = value

    def setMirrorAppearance(self, value):
        self.mirrorAppearance = value

    def setMirrorAllowCreate(self, value):
        self.mirrorAllowCreate = value

    def __init__(self, parent):
        super(SymmetryPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "Symmetry"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        self.setupContentUi(frame)

    def setupContentUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        # mirror settings
        # ---------------

        check = QtWidgets.QCheckBox(parent)
        check.setText("Include All Children")
        check.setStatusTip(
            "Recursively mirror the selected nodes and all of their children")
        check.setChecked(self.mirrorRecursive)
        check.stateChanged.connect(
            self.setMirrorRecursive)
        layout.addWidget(check)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Transforms")
        check.setStatusTip(
            "Mirror the transform matrices of the nodes")
        check.setChecked(self.mirrorTransforms)
        check.stateChanged.connect(
            self.setMirrorTransforms)
        layout.addWidget(check)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Parenting")
        check.setStatusTip(
            "Mirror the parenting structure of the nodes")
        check.setChecked(self.mirrorParenting)
        check.stateChanged.connect(
            self.setMirrorParenting)
        layout.addWidget(check)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Appearance")
        check.setStatusTip(
            "Mirror the name and color of the nodes")
        check.setChecked(self.mirrorAppearance)
        check.stateChanged.connect(
            self.setMirrorAppearance)
        layout.addWidget(check)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Allow Node Creation")
        check.setStatusTip(
            "Allow the creation of nodes when mirroring recursively")
        check.setChecked(self.mirrorAllowCreate)
        check.stateChanged.connect(
            self.setMirrorAllowCreate)
        layout.addWidget(check)

        # mirror axis

        # mirror mode toggle

        # mirror actions
        # --------------
        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        pairBtn = QtWidgets.QPushButton(parent)
        pairBtn.setText("Pair")
        pairBtn.setStatusTip(
            "Pair the two selected nodes as mirroring counterparts")
        pairBtn.clicked.connect(cmd(editorutils.pairSelected))

        unpairBtn = QtWidgets.QPushButton(parent)
        unpairBtn.setText("Unpair")
        unpairBtn.setStatusTip(
            "Unpair the selected node or nodes (can be many at once)")
        unpairBtn.clicked.connect(cmd(editorutils.unpairSelected))

        mirrorBtn = QtWidgets.QPushButton(parent)
        mirrorBtn.setText("Mirror")
        mirrorBtn.setStatusTip(
            "Mirror the selected nodes using the current options")
        mirrorBtn.clicked.connect(self.mirrorSelected)

        gridItems = [
            [pairBtn, unpairBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)
        gridLayout.addWidget(mirrorBtn, 2, 0, 1, 2)
        layout.addLayout(gridLayout)

    def mirrorSelected(self):
        kw = dict(
            recursive=self.mirrorRecursive,
            create=self.mirrorAllowCreate,
            curveShapes=True,
            links=True,
            reparent=self.mirrorParenting,
            transform=self.mirrorTransforms,
            appearance=self.mirrorAppearance,
        )
        cmd(editorutils.mirrorSelected, **kw)()
