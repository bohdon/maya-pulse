
import pymel.core as pm
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse.core
from .core import PulseWindow, BlueprintUIModel
from .utils import undoAndRepeatPartial as cmd
from . import style

__all__ = [
    "QuickColorWidget",
    "QuickColorWindow",
]


class QuickColorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(QuickColorWidget, self).__init__(parent=parent)


class QuickColorWindow(PulseWindow):

    OBJECT_NAME = 'pulseQuickColorWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.quickcolor'

    def __init__(self, parent=None):
        super(QuickColorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Quick Color Editor')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.setLayout(layout)

        widget = QuickColorWidget(self)
        layout.addWidget(widget)
