
from Qt import QtCore, QtWidgets, QtGui
import pymetanode as meta

import pulse
from pulse.views.core import PulseWindow


__all__ = [
    'ActionEditorWidget',
    'ActionEditorWindow',
]


class ActionEditorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ActionEditorWidget, self).__init__(parent=parent)

        layout = QtWidgets.QVBoxLayout(self)


class ActionEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseActionEditorWindow'

    def __init__(self, parent=None):
        super(ActionEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Editor')

        widget = ActionEditorWidget(self)
        self.setCentralWidget(widget)
