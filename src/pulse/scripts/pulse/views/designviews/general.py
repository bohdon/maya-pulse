
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

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
        gridLayout.addWidget(freezeScaleBtn, 0, 0, 1, 1)

        freezePivotBtn = QtWidgets.QPushButton(parent)
        freezePivotBtn.setText("Freeze Pivot")
        gridLayout.addWidget(freezePivotBtn, 0, 1, 1, 1)

        parentSelBtn = QtWidgets.QPushButton(parent)
        parentSelBtn.setText("Parent Selected")
        gridLayout.addWidget(parentSelBtn, 1, 0, 1, 1)

        createOffsetBtn = QtWidgets.QPushButton(parent)
        createOffsetBtn.setText("Create Offset")
        gridLayout.addWidget(createOffsetBtn, 1, 1, 1, 1)

        parentInOrderBtn = QtWidgets.QPushButton(parent)
        parentInOrderBtn.setText("Parent in Order")
        gridLayout.addWidget(parentInOrderBtn, 2, 0, 1, 1)

        selectChildrenBtn = QtWidgets.QPushButton(parent)
        selectChildrenBtn.setText("Select Children")
        gridLayout.addWidget(selectChildrenBtn, 2, 1, 1, 1)

        layout.addLayout(gridLayout)
