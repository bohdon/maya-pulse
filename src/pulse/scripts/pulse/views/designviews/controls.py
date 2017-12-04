
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse.shapes
import pulse.controlshapes

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

        pulse.controlshapes.loadBuiltinControlShapes()

        def createControlShapeButton(text, shapeData):
            btn = QtWidgets.QPushButton(parent)
            btn.setText(text)
            btn.setStatusTip("Create a new control")
            btn.clicked.connect(buttonCommand(pulse.controlshapes.createControlsForSelected, shapeData))
            return btn

        shapes = pulse.controlshapes.getControlShapes()

        for s in shapes:
            btn = createControlShapeButton(s['name'], s)
            gridLayout.addWidget(btn)
            
    
    def setupEditControlsUi(self, parent):
        layout = QtWidgets.QHBoxLayout(parent)
        layout.setSpacing(2)
        
        def createRotateComponentsButton(text, color, axis, degrees):
            btn = QtWidgets.QPushButton(parent)
            btn.setText(text)
            btn.setStatusTip('Rotate the components of the selected controls {0} degrees around the {1} axis'.format(degrees, {0:'X', 1:'Y', 2:'Z'}[axis]))
            self.setPresetColor(btn, color)
            btn.clicked.connect(buttonCommand(pulse.shapes.rotateSelectedComponentsAroundAxis, axis, degrees))
            return btn

        btn = createRotateComponentsButton('- X', 'red', 0, -90)
        layout.addWidget(btn)
        btn = createRotateComponentsButton('+ X', 'red', 0, 90)
        layout.addWidget(btn)
        btn = createRotateComponentsButton('- Y', 'green', 1, -90)
        layout.addWidget(btn)
        btn = createRotateComponentsButton('+ Y', 'green', 1, 90)
        layout.addWidget(btn)
        btn = createRotateComponentsButton('- Z', 'blue', 2, -90)
        layout.addWidget(btn)
        btn = createRotateComponentsButton('+ Z', 'blue', 2, 90)
        layout.addWidget(btn)
