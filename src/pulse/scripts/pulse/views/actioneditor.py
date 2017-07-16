
from Qt import QtCore, QtWidgets, QtGui
import pymetanode as meta

import pulse
from pulse.views.core import PulseWindow
from pulse.views.actiontree import ActionTreeSelectionModel


__all__ = [
    'ActionEditorWidget',
    'ActionEditorWindow',
]


class ActionEditorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ActionEditorWidget, self).__init__(parent=parent)

        self.selectionModel = ActionTreeSelectionModel.getSharedModel()

        layout = QtWidgets.QVBoxLayout(self)

        self.selectionModel.selectionChanged.connect(self.selectionChanged)

    def selectionChanged(self, selected, deselected):
        print(selected, deselected)


class ActionEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseActionEditorWindow'

    def __init__(self, parent=None):
        super(ActionEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Editor')

        widget = ActionEditorWidget(self)
        self.setCentralWidget(widget)
