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

        self.setup_ui(self)

    def setup_ui(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        self.setLayout(layout)

        copy_btn = QtWidgets.QPushButton(parent)
        copy_btn.setText("Copy")
        copy_btn.setStatusTip("Copy the world matrices of the selected nodes")
        copy_btn.clicked.connect(self.copy_selected)
        layout.addWidget(copy_btn)

        paste_btn = QtWidgets.QPushButton(parent)
        paste_btn.setText("Paste")
        copy_btn.setStatusTip("Paste copied matrices onto the selected nodes")
        paste_btn.clicked.connect(self.paste_selected)
        layout.addWidget(paste_btn)

        relative_copy_btn = QtWidgets.QPushButton(parent)
        relative_copy_btn.setText("Relative Copy")
        copy_btn.setStatusTip("Copy the relative matrices of the selected nodes")
        relative_copy_btn.clicked.connect(self.relative_copy_selected)
        layout.addWidget(relative_copy_btn)

        relative_paste_btn = QtWidgets.QPushButton(parent)
        relative_paste_btn.setText("Relative Paste")
        copy_btn.setStatusTip(
            "Paste copied matrices on the selected nodes relative "
            "to the node used during copy or first selected node"
        )
        relative_paste_btn.clicked.connect(self.relative_paste_selected)
        layout.addWidget(relative_paste_btn)

    def copy_selected(self):
        sel = pm.selected()
        if not sel:
            LOG.warning("nothing selected")
            return

        self.copy(sel)

    def relative_copy_selected(self):
        sel = pm.selected()
        if len(sel) < 2:
            LOG.warning("must select at least one base node, followed by " "any number of nodes to copy ")
            return

        self.copy(sel[1:], base_node=sel[0])

    def paste_selected(self):
        sel = pm.selected()

        if not sel:
            LOG.warning("nothing selected")
            return

        self.paste_over_time(sel)

    def relative_paste_selected(self):
        sel = pm.selected()

        if not sel:
            LOG.warning("nothing selected")
            return

        base_node = self.clipboard.get("base_node", None)

        if len(sel) > self.num_copied():
            # use first object in selection as the new base node
            base_node = sel[0]
            sel = sel[1:]

        if not base_node:
            LOG.warning("No base node could be found for relative paste")
            return

        self.paste_over_time(sel, base_node)

    def num_copied(self):
        """
        Return the number of node matrices in the clipboard
        """
        return len(self.clipboard.get("matrices", []))

    def copy(self, transforms, base_node=None):
        """
        Copy the matrices for the given node or nodes.

        Args:
            transforms (list of PyNode): A list of transform nodes
            base_node (PyNode): If given, copies the matrices
                relative to this node
        """
        self.clipboard = {}
        if base_node is not None:
            self.clipboard["base_node"] = base_node
            self.clipboard["matrices"] = [nodes.get_relative_matrix(n, base_node) for n in transforms]
            LOG.debug("copied relative to {0}".format(base_node))
        else:
            self.clipboard["matrices"] = [nodes.get_world_matrix(n) for n in transforms]

    def paste_over_time(self, transforms, base_node=None):
        """
        Paste the copied matrices onto the given nodes,
        If a time range is selected, pastes the matrices on every frame.
        """
        time_range = None
        # timeRange = utils.getSelectedTimeRange()

        if time_range is not None:
            pass
            # for f in timeRange.times:
            #     pm.currentTime(f)
            #     self.paste(sel, relative=relative, base_node=relObj)
            #     pm.setKeyframe(sel, at=['t', 'r', 's'])
        else:
            self.paste(transforms, base_node=base_node)

    def paste(self, transforms, base_node=None):
        """
        Paste the copied matrix/matrices onto all the given nodes.

        Args:
            transforms (list of PyNode): The nodes to modify
            base_node (PyNode): If given, apply matrices relative to this node
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

        if base_node:
            # relative paste
            # zipping clamps to the shortest list
            for matrix, node in zip(matrices, transforms):
                if node and node == base_node:
                    LOG.warning("cannot paste a matrix " "relative to itself: {0}".format(node))
                    continue
                LOG.debug("pasting relative to {0}".format(base_node))
                nodes.set_relative_matrix(node, matrix, base_node)
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
