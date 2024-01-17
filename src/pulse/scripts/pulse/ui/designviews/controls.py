from PySide2 import QtCore, QtWidgets

from ..utils import get_icon
from ..utils import undo_and_repeat_partial as cmd
from ... import control_shapes
from ... import editor_utils


class ControlsDesignPanel(QtWidgets.QWidget):
    def __init__(self, parent):
        super(ControlsDesignPanel, self).__init__(parent)

        self.setup_ui(self)

    def setup_ui(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)
        layout.setSpacing(4)

        create_layout = QtWidgets.QGridLayout(parent)
        create_layout.setMargin(0)
        create_layout.setSpacing(2)

        control_shapes.load_builtin_control_shapes()

        def _create_control_shape_button(text, shape_data):
            _btn = QtWidgets.QPushButton(parent)
            _btn.setStatusTip("Create a new control")
            if "icon" in shape_data:
                _btn.setIcon(get_icon("controls/" + shape_data["icon"]))
                _btn.setIconSize(QtCore.QSize(32, 32))
            else:
                _btn.setText(text)
            _btn.clicked.connect(cmd(control_shapes.create_controls_for_selected, shape_data))
            return _btn

        shapes = control_shapes.get_control_shapes()

        row = 0
        col = 0
        column_count = 4
        for s in shapes:
            btn = _create_control_shape_button(s["name"], s)
            create_layout.addWidget(btn, row, col, 1, 1)
            col += 1
            if col == column_count:
                row += 1
                col = 0

        layout.addLayout(create_layout)

        # setup edit controls ui
        edit_layout = QtWidgets.QHBoxLayout(parent)
        edit_layout.setMargin(0)
        edit_layout.setSpacing(2)

        def _create_rotate_components_button(text, css_classes: str, axis, degrees):
            _axes = {0: "X", 1: "Y", 2: "Z"}

            _btn = QtWidgets.QPushButton(parent)
            _btn.setText(text)
            _btn.setStatusTip(
                "Rotate the components of the selected controls " f"{degrees} degrees around the {_axes[axis]} axis"
            )
            _btn.setProperty("cssClasses", css_classes)

            _btn.clicked.connect(cmd(editor_utils.rotate_selected_components_around_axis, axis, degrees))
            edit_layout.addWidget(_btn)

        _create_rotate_components_button("- X", "x-axis", 0, -90)
        _create_rotate_components_button("+ X", "x-axis", 0, 90)
        _create_rotate_components_button("- Y", "y-axis", 1, -90)
        _create_rotate_components_button("+ Y", "y-axis", 1, 90)
        _create_rotate_components_button("- Z", "z-axis", 2, -90)
        _create_rotate_components_button("+ Z", "z-axis", 2, 90)

        layout.addLayout(edit_layout)
