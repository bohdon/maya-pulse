"""
Widget for quickly editing the color of animation controls.
"""

from PySide2 import QtWidgets

from .core import PulseWindow, BlueprintUIModel
from .gen.quick_color_editor import Ui_QuickColorEditor
from .utils import undo_and_repeat_partial as cmd
from .. import editor_utils
from ..colors import LinearColor


class QuickColorEditor(QtWidgets.QWidget):
    """
    Widget for quickly editing the color of animation controls.
    """

    def __init__(self, parent=None):
        super(QuickColorEditor, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.get_default_model()

        # the blueprint config
        self.config = self.blueprintModel.blueprint.get_config()
        # the section of the config containing all colors
        self.colors_config = self.config.get("colors", {})

        self.ui = Ui_QuickColorEditor()
        self.ui.setupUi(self)
        self.setup_color_buttons_ui(self)

        self.ui.remove_btn.clicked.connect(cmd(editor_utils.disable_color_override_for_selected))
        self.ui.edit_config_btn.clicked.connect(editor_utils.open_blueprint_config_in_source_editor)

    def setup_color_buttons_ui(self, parent):
        row, col = 0, 0
        num_cols = 5
        for name, hex_color in self.colors_config.items():
            color = LinearColor.from_hex(hex_color)
            btn = self._create_color_button(name, color, parent)
            self.ui.color_btns_layout.addWidget(btn, row, col)
            col += 1
            if col > num_cols:
                col = 0
                row += 1

    def _create_color_button(self, name: str, color: LinearColor, parent):
        btn = QtWidgets.QToolButton(parent)
        btn.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        btn.setMinimumHeight(30)
        btn.setText(name)
        # btn.setStyleSheet(color.as_fg_style())
        btn.setStyleSheet(f"border: 2px solid {color.as_style()}")
        btn.clicked.connect(cmd(editor_utils.set_override_color_for_selected, color))
        return btn


class QuickColorWindow(PulseWindow):
    OBJECT_NAME = "pulseQuickColorWindow"
    WINDOW_MODULE = "pulse.ui.quickcolor"
    WINDOW_TITLE = "Quick Color Editor"
    WIDGET_CLASS = QuickColorEditor
