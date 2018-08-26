
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm

import pulse.nodes
import pulse.sym

from pulse.views.utils import undoAndRepeatPartial as cmd
from .core import DesignViewPanel

__all__ = [
    "SymmetryPanel",
]


class SymmetryPanel(DesignViewPanel):

    def __init__(self, parent):
        super(SymmetryPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "Symmetry"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        gridLayout = QtWidgets.QGridLayout(frame)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        # mirror axis

        # mirror mode toggle

        # pair / unpair

        # mirror transforms / parenting / action data / all

        # cleanup
        pairBtn = QtWidgets.QPushButton(frame)
        pairBtn.setText("Pair")
        pairBtn.setStatusTip(
            "Pair the two selected nodes as mirroring counterparts")
        pairBtn.clicked.connect(cmd(self.pairSelected))
        gridLayout.addWidget(pairBtn, 0, 0, 1, 1)

        unpairBtn = QtWidgets.QPushButton(frame)
        unpairBtn.setText("Unpair")
        unpairBtn.setStatusTip(
            "Unpair the selected node or nodes (can be many at once)")
        unpairBtn.clicked.connect(cmd(self.unpairSelected))
        gridLayout.addWidget(unpairBtn, 0, 1, 1, 1)

        mirrorTransformsBtn = QtWidgets.QPushButton(frame)
        mirrorTransformsBtn.setText("Mirror Transforms")
        mirrorTransformsBtn.setStatusTip(
            "Mirror transforms of the selected nodes")
        mirrorTransformsBtn.clicked.connect(cmd(self.mirrorTransforms))
        gridLayout.addWidget(mirrorTransformsBtn, 1, 0, 1, 1)

        mirrorParentBtn = QtWidgets.QPushButton(frame)
        mirrorParentBtn.setText("Mirror Parenting")
        mirrorParentBtn.setStatusTip(
            "Mirror the parenting hierarchy of the selected nodes")
        mirrorParentBtn.clicked.connect(cmd(self.mirrorParenting))
        gridLayout.addWidget(mirrorParentBtn, 1, 1, 1, 1)

        mirrorAllBtn = QtWidgets.QPushButton(frame)
        mirrorAllBtn.setText("Mirror All")
        mirrorAllBtn.setStatusTip(
            "Mirror all aspects of the selected nodes")
        mirrorAllBtn.clicked.connect(cmd(self.mirrorAll))
        gridLayout.addWidget(mirrorAllBtn, 2, 0, 1, 1)

        mirrorActionsBtn = QtWidgets.QPushButton(frame)
        mirrorActionsBtn.setText("Mirror Actions")
        mirrorActionsBtn.setStatusTip(
            "Mirror the Pulse Actions associated with the selected nodes")
        mirrorActionsBtn.clicked.connect(cmd(self.mirrorActions))
        gridLayout.addWidget(mirrorActionsBtn, 2, 1, 1, 1)

        self.includeChildrenCheck = QtWidgets.QCheckBox(frame)
        self.includeChildrenCheck.setText("Include All Children")
        layout.addWidget(self.includeChildrenCheck)

    def isRecursive(self):
        return self.includeChildrenCheck.isChecked()

    def pairSelected(self):
        sel = pm.selected()
        if len(sel) == 2:
            pulse.sym.pairMirrorNodes(sel[0], sel[1])

    def unpairSelected(self):
        for s in pm.selected():
            pulse.sym.unpairMirrorNode(s)

    def mirrorAll(self):
        util = pulse.sym.MirrorUtil()
        fnc = util.mirrorRecursive if self.isRecursive() else util.mirror
        fnc(pm.selected())

    def mirrorTransforms(self):
        util = pulse.sym.MirrorUtil()
        fnc = util.mirrorRecursive if self.isRecursive() else util.mirror
        fnc(pm.selected(), create=False, reparent=False, transform=True)

    def mirrorParenting(self):
        util = pulse.sym.MirrorUtil()
        fnc = util.mirrorRecursive if self.isRecursive() else util.mirror
        fnc(pm.selected(), create=False, reparent=True, transform=False)

    def mirrorActions(self):
        pass
