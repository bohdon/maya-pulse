import logging

import pymel.core as pm

from .core import PulseWindow
from .. import nodes
from ..vendor.Qt import QtCore, QtWidgets

LOG = logging.getLogger(__name__)


class CopyPasteMatrixWidget(QtWidgets.QWidget):
    """
    A util widget that contains a clipboard for copying and pasting
    transform matrices between objects.
    """

    def __init__(self, parent=None):
        super(CopyPasteMatrixWidget, self).__init__(parent=parent)

        # contains copied matrix data
        self.clipboard = {}

        self.setupUi(self)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        self.setLayout(layout)

        copyBtn = QtWidgets.QPushButton(parent)
        copyBtn.setText("Copy")
        copyBtn.setStatusTip("Copy the world matrices of the selected nodes")
        copyBtn.clicked.connect(self.copySelected)
        layout.addWidget(copyBtn)

        pasteBtn = QtWidgets.QPushButton(parent)
        pasteBtn.setText("Paste")
        copyBtn.setStatusTip("Paste copied matrices onto the selected nodes")
        pasteBtn.clicked.connect(self.pasteSelected)
        layout.addWidget(pasteBtn)

        relativeCopyBtn = QtWidgets.QPushButton(parent)
        relativeCopyBtn.setText("Relative Copy")
        copyBtn.setStatusTip("Copy the relative matrices of the selected nodes")
        relativeCopyBtn.clicked.connect(self.relativeCopySelected)
        layout.addWidget(relativeCopyBtn)

        relativePasteBtn = QtWidgets.QPushButton(parent)
        relativePasteBtn.setText("Relative Paste")
        copyBtn.setStatusTip(
            "Paste copied matrices on the selected nodes relative "
            "to the node used during copy or first selected node"
        )
        relativePasteBtn.clicked.connect(self.relativePasteSelected)
        layout.addWidget(relativePasteBtn)

    def copySelected(self):
        sel = pm.selected()
        if not sel:
            LOG.warning("nothing selected")
            return

        self.copy(sel)

    def relativeCopySelected(self):
        sel = pm.selected()
        if len(sel) < 2:
            LOG.warning("must select at least one base node, followed by " "any number of nodes to copy ")
            return

        self.copy(sel[1:], baseNode=sel[0])

    def pasteSelected(self):
        sel = pm.selected()

        if not sel:
            LOG.warning("nothing selected")
            return

        self.pasteOverTime(sel)

    def relativePasteSelected(self):
        sel = pm.selected()

        if not sel:
            LOG.warning("nothing selected")
            return

        base_node = self.clipboard.get("baseNode", None)

        if len(sel) > self.numCopied():
            # use first object in selection as the new base node
            base_node = sel[0]
            sel = sel[1:]

        if not base_node:
            LOG.warning("No base node could be found for relative paste")
            return

        self.pasteOverTime(sel, base_node)

    def numCopied(self):
        """
        Return the number of node matrices in the clipboard
        """
        return len(self.clipboard.get("matrices", []))

    def copy(self, transforms, baseNode=None):
        """
        Copy the matrices for the given node or nodes.

        Args:
            transforms (list of PyNode): A list of transform nodes
            baseNode (PyNode): If given, copies the matrices
                relative to this node
        """
        self.clipboard = {}
        if baseNode is not None:
            self.clipboard["baseNode"] = baseNode
            self.clipboard["matrices"] = [nodes.get_relative_matrix(n, baseNode) for n in transforms]
            LOG.debug("copied relative to {0}".format(baseNode))
        else:
            self.clipboard["matrices"] = [nodes.get_world_matrix(n) for n in transforms]

    def pasteOverTime(self, transforms, base_node=None):
        """
        Paste the copied matrices onto the given nodes,
        If a time range is selected, pastes the matrices on every frame.
        """
        timeRange = None
        # timeRange = utils.getSelectedTimeRange()

        if timeRange is not None:
            pass
            # for f in timeRange.times:
            #     pm.currentTime(f)
            #     self.paste(sel, relative=relative, base_node=relObj)
            #     pm.setKeyframe(sel, at=['t', 'r', 's'])
        else:
            self.paste(transforms, baseNode=base_node)

    def paste(self, transforms, baseNode=None):
        """
        Paste the copied matrix/matrices onto all the given nodes.

        Args:
            transforms (list of PyNode): The nodes to modify
            baseNode (PyNode): If given, apply matrices relative to this node
        """
        if not self.clipboard:
            return LOG.warning("nothing has been copied")

        # resolve 1 to many or many to many matrices
        matrices = self.clipboard.get("matrices", [])
        if len(matrices) < len(transforms):
            if len(matrices) == 1:
                # expand matrices list to be the same for each node
                matrices = [matrices[0] for _ in range(len(transforms))]
            else:
                # more nodes were selected than matrices copied
                LOG.warning(
                    "trying to paste {0} matrices "
                    "onto {1} nodes, will skip the last nodes".format(len(matrices), len(transforms))
                )

        if baseNode:
            # relative paste
            # zipping clamps to the shortest list
            for matrix, node in zip(matrices, transforms):
                if node and node == baseNode:
                    LOG.warning("cannot paste a matrix " "relative to itself: {0}".format(node))
                    continue
                LOG.debug("pasting relative to {0}".format(baseNode))
                nodes.set_relative_matrix(node, matrix, baseNode)
        else:
            # normal paste
            for matrix, node in zip(matrices, transforms):
                nodes.set_world_matrix(node, matrix)


class CopyPasteMatrixWindow(PulseWindow):
    OBJECT_NAME = "pulseCopyPasteMatrixWindow"
    PREFERRED_SIZE = QtCore.QSize(220, 160)
    STARTING_SIZE = QtCore.QSize(220, 160)
    MINIMUM_SIZE = QtCore.QSize(220, 160)
    REQUIRED_PLUGINS = []
    WINDOW_MODULE = "pulse.ui.utilviews"

    def __init__(self, parent=None):
        super(CopyPasteMatrixWindow, self).__init__(parent=parent)

        self.setWindowTitle("Copy Paste Matrix")

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        widget = CopyPasteMatrixWidget(self)
        layout.addWidget(widget)
