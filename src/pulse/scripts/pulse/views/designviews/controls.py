
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse.shapes

from pulse.views.core import buttonCommand
from .core import DesignViewPanel

__all__ = [
    "ControlsPanel",
]


class ControlsPanel(DesignViewPanel):

    def __init__(self, parent):
        super(ControlsPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "Controls"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        createFrame = self.createPanelFrame(parent)
        layout.addWidget(createFrame)
        self.setupCreateControlsUi(createFrame)

        editFrame = self.createPanelFrame(parent)
        layout.addWidget(editFrame)
        self.setupEditControlsUi(editFrame)
    
    def setupCreateControlsUi(self, parent):
        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setSpacing(4)
    
    def setupEditControlsUi(self, parent):
        layout = QtWidgets.QHBoxLayout(parent)
        layout.setSpacing(2)

        btn = QtWidgets.QPushButton(parent)
        btn.setText('- X')
        btn.clicked.connect(buttonCommand(pulse.shapes.rotateSelectedComponentsAroundAxis, 0, -90))
        self.setPresetColor(btn, 'red')
        layout.addWidget(btn)

        btn = QtWidgets.QPushButton(parent)
        btn.setText('+ X')
        btn.clicked.connect(buttonCommand(pulse.shapes.rotateSelectedComponentsAroundAxis, 0, 90))
        self.setPresetColor(btn, 'red')
        layout.addWidget(btn)

        btn = QtWidgets.QPushButton(parent)
        btn.setText('- Y')
        btn.clicked.connect(buttonCommand(pulse.shapes.rotateSelectedComponentsAroundAxis, 1, -90))
        self.setPresetColor(btn, 'green')
        layout.addWidget(btn)

        btn = QtWidgets.QPushButton(parent)
        btn.setText('+ Y')
        btn.clicked.connect(buttonCommand(pulse.shapes.rotateSelectedComponentsAroundAxis, 1, 90))
        self.setPresetColor(btn, 'green')
        layout.addWidget(btn)

        btn = QtWidgets.QPushButton(parent)
        btn.setText('- Z')
        btn.clicked.connect(buttonCommand(pulse.shapes.rotateSelectedComponentsAroundAxis, 2, -90))
        self.setPresetColor(btn, 'blue')
        layout.addWidget(btn)

        btn = QtWidgets.QPushButton(parent)
        btn.setText('+ Z')
        btn.clicked.connect(buttonCommand(pulse.shapes.rotateSelectedComponentsAroundAxis, 2, 90))
        self.setPresetColor(btn, 'blue')
        layout.addWidget(btn)
