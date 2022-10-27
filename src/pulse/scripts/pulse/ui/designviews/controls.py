from ..utils import getIcon
from ..utils import undoAndRepeatPartial as cmd
from ... import controlshapes
from ... import editorutils
from ...vendor.Qt import QtCore, QtWidgets


class ControlsDesignPanel(QtWidgets.QWidget):

    def __init__(self, parent):
        super(ControlsDesignPanel, self).__init__(parent)

        self.setupUi(self)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)
        layout.setSpacing(4)

        create_layout = QtWidgets.QGridLayout(parent)
        create_layout.setMargin(0)
        create_layout.setSpacing(2)

        controlshapes.load_builtin_control_shapes()

        def createControlShapeButton(text, shapeData):
            btn = QtWidgets.QPushButton(parent)
            btn.setStatusTip("Create a new control")
            if 'icon' in shapeData:
                btn.setIcon(getIcon("controls/" + shapeData["icon"]))
                btn.setIconSize(QtCore.QSize(32, 32))
            else:
                btn.setText(text)
            btn.clicked.connect(cmd(controlshapes.create_controls_for_selected, shapeData))
            return btn

        shapes = controlshapes.get_control_shapes()

        row = 0
        col = 0
        columnCount = 4
        for s in shapes:
            btn = createControlShapeButton(s['name'], s)
            create_layout.addWidget(btn, row, col, 1, 1)
            col += 1
            if col == columnCount:
                row += 1
                col = 0

        layout.addLayout(create_layout)

        # setup edit controls ui
        edit_layout = QtWidgets.QHBoxLayout(parent)
        edit_layout.setMargin(0)
        edit_layout.setSpacing(2)

        def createRotateComponentsButton(text, cssClasses: str, axis, degrees):
            _axes = {0: 'X', 1: 'Y', 2: 'Z'}

            btn = QtWidgets.QPushButton(parent)
            btn.setText(text)
            btn.setStatusTip("Rotate the components of the selected controls "
                             f"{degrees} degrees around the {_axes[axis]} axis")
            btn.setProperty('cssClasses', cssClasses)

            btn.clicked.connect(cmd(editorutils.rotate_selected_components_around_axis, axis, degrees))
            edit_layout.addWidget(btn)

        createRotateComponentsButton('- X', 'x-axis', 0, -90)
        createRotateComponentsButton('+ X', 'x-axis', 0, 90)
        createRotateComponentsButton('- Y', 'y-axis', 1, -90)
        createRotateComponentsButton('+ Y', 'y-axis', 1, 90)
        createRotateComponentsButton('- Z', 'z-axis', 2, -90)
        createRotateComponentsButton('+ Z', 'z-axis', 2, 90)

        layout.addLayout(edit_layout)
