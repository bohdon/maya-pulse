"""
Widget for quickly editing the color of animation controls.
"""

from ..vendor.Qt import QtCore, QtWidgets
from .. import editorutils
from ..colors import LinearColor
from .core import PulseWindow, BlueprintUIModel
from .utils import undoAndRepeatPartial as cmd
from .gen.quick_color_editor import Ui_QuickColorEditor


class QuickColorEditor(QtWidgets.QWidget):
    """
    Widget for quickly editing the color of animation controls.
    """

    def __init__(self, parent=None):
        super(QuickColorEditor, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        # the blueprint config
        self.config = self.blueprintModel.blueprint.get_config()
        # the section of the config containing all colors
        self.colors_config = self.config.get('colors', {})

        self.ui = Ui_QuickColorEditor()
        self.ui.setupUi(self)
        self.setupColorButtonsUi(self)

        self.ui.remove_btn.clicked.connect(cmd(editorutils.disable_color_override_for_selected))
        self.ui.edit_config_btn.clicked.connect(editorutils.open_blueprint_config_in_source_editor)

    def setupColorButtonsUi(self, parent):
        row, col = 0, 0
        num_cols = 5
        for name, hex_color in self.colors_config.items():
            color = LinearColor.from_hex(hex_color)
            btn = self._createColorButton(name, color, parent)
            self.ui.color_btns_layout.addWidget(btn, row, col)
            col += 1
            if col > num_cols:
                col = 0
                row += 1

    def _createColorButton(self, name: str, color: LinearColor, parent):
        btn = QtWidgets.QToolButton(parent)
        btn.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        btn.setMinimumHeight(30)
        btn.setText(name)
        # btn.setStyleSheet(color.as_fg_style())
        btn.setStyleSheet(f'border: 2px solid {color.as_style()}')
        btn.clicked.connect(cmd(editorutils.set_override_color_for_selected, color))
        return btn


class QuickColorWindow(PulseWindow):
    OBJECT_NAME = 'pulseQuickColorWindow'
    WINDOW_MODULE = 'pulse.ui.quickcolor'
    WINDOW_TITLE = 'Quick Color Editor'
    WIDGET_CLASS = QuickColorEditor
