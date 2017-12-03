
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm

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
        parentSelBtn.clicked.connect(buttonCommand(pulse.nodes.parentSelected))
        gridLayout.addWidget(parentSelBtn, 1, 0, 1, 1)

        parentInOrderBtn = QtWidgets.QPushButton(parent)
        parentInOrderBtn.setText("Parent in Order")
        parentInOrderBtn.setStatusTip("Parent the selection in order, select leaders to followers")
        parentInOrderBtn.clicked.connect(buttonCommand(pulse.nodes.parentSelectedInOrder))
        gridLayout.addWidget(parentInOrderBtn, 1, 1, 1, 1)

        createOffsetBtn = QtWidgets.QPushButton(parent)
        createOffsetBtn.setText("Create Offset")
        createOffsetBtn.setStatusTip("Group the selected transform, creating the group exactly where the transform is")
        createOffsetBtn.clicked.connect(buttonCommand(pulse.nodes.createOffsetForSelected))
        gridLayout.addWidget(createOffsetBtn, 2, 0, 1, 1)

        selectChildrenBtn = QtWidgets.QPushButton(parent)
        selectChildrenBtn.setText("Select Children")
        selectChildrenBtn.setStatusTip("Select all descendants of the selected node")
        selectChildrenBtn.clicked.connect(buttonCommand(self.selectChildren))
        gridLayout.addWidget(selectChildrenBtn, 2, 1, 1, 1)

        layout.addLayout(gridLayout)

    def selectChildren(self):
        """
        Select all child nodes. Similar to select hierarchy except
        only transforms or joints are selected.
        """
        objs = []
        for obj in pm.selected():
            objs.extend(obj.listRelatives(ad=True, type=['transform', 'joint']))
        pm.select(objs, add=True)
