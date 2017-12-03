
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse.nodes

from pulse.views.core import buttonCommand
from .core import DesignViewPanel

__all__ = [
    "GeneralPanel",
]


class GeneralPanel(DesignViewPanel):

    def __init__(self, parent):
        super(GeneralPanel, self).__init__(parent=parent)

        self.setupUi(self)

    def getPanelDisplayName(self):
        return "General"

    def setupUi(self, parent):
        layout, parent = self.setupPanelUi(parent)

        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setSpacing(4)

        freezeScaleBtn = QtWidgets.QPushButton(parent)
        freezeScaleBtn.setText("Freeze Scales")
        freezeScaleBtn.setStatusTip("Freeze the scales of the selected node and its children without affecting their pivots")
        freezeScaleBtn.clicked.connect(buttonCommand(pulse.nodes.freezeScalesForSelectedHierarchies))
        gridLayout.addWidget(freezeScaleBtn, 0, 0, 1, 1)

        freezePivotBtn = QtWidgets.QPushButton(parent)
        freezePivotBtn.setText("Freeze Pivots")
        freezePivotBtn.setStatusTip("Freeze the local pivots of the selected node and its children by baking the values into translate")
        freezePivotBtn.clicked.connect(buttonCommand(pulse.nodes.freezePivotsForSelectedHierarchies))
        gridLayout.addWidget(freezePivotBtn, 0, 1, 1, 1)

        parentSelBtn = QtWidgets.QPushButton(parent)
        parentSelBtn.setText("Parent Selected")
        parentSelBtn.setStatusTip("Parent the selected nodes, select one leader then followers")
        gridLayout.addWidget(parentSelBtn, 1, 0, 1, 1)

        createOffsetBtn = QtWidgets.QPushButton(parent)
        createOffsetBtn.setText("Create Offset")
        createOffsetBtn.setStatusTip("Group the selected transform, creating the group exactly where the transform is")
        gridLayout.addWidget(createOffsetBtn, 1, 1, 1, 1)

        parentInOrderBtn = QtWidgets.QPushButton(parent)
        parentInOrderBtn.setText("Parent in Order")
        parentInOrderBtn.setStatusTip("Parent the selection in order, select leaders to followers")
        gridLayout.addWidget(parentInOrderBtn, 2, 0, 1, 1)

        selectChildrenBtn = QtWidgets.QPushButton(parent)
        selectChildrenBtn.setText("Select Children")
        gridLayout.addWidget(selectChildrenBtn, 2, 1, 1, 1)

        layout.addLayout(gridLayout)
