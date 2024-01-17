"""
Animation tools for working with keyframes and the graph editor.
"""
import logging

import pymel.core as pm
from PySide2 import QtWidgets

from ..core import PulseWindow
from ..gen.anim_tools import Ui_AnimTools
from ..utils import undo_and_repeat_partial as cmd

logger = logging.getLogger(__name__)

PICKER_METACLASS = "pulse_animpicker"


class AnimToolsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.ui = Ui_AnimTools()
        self.ui.setupUi(self)

        self.ui.move_keys_btn.clicked.connect(cmd(self.move_selected_keys))

    def move_selected_keys(self):
        delta_value = self.ui.move_keys_spin_box.value()
        pm.keyframe(edit=True, includeUpperBound=True, relative=True, option="over", valueChange=delta_value)


class AnimToolsWindow(PulseWindow):
    OBJECT_NAME = "pulseAnimToolsWindow"
    WINDOW_MODULE = "pulse.ui.anim.tools"
    WINDOW_TITLE = "Anim Tools"
    WIDGET_CLASS = AnimToolsWidget
