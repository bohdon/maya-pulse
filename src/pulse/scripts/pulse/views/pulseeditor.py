
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse
from pulse.views.core import PulseWindow
from pulse.views.blueprinteditor import BlueprintEditorWidget
from pulse.views.actiontree import ActionTreeWidget
from pulse.views.actiontree import ActionButtonsWidget
from pulse.views.actioneditor import ActionEditorWidget


__all__ = [
    'PulseEditorWindow',
]


class PulseEditorWindow(PulseWindow):
    """
    An all-in-one window that contains all pulse editors.
    """

    OBJECT_NAME = 'pulseEditorWindow'

    def __init__(self, parent=None):
        super(PulseEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse')

        pulse.loadBuiltinActions()

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)

        layout = QtWidgets.QVBoxLayout(self)
        widget.setLayout(layout)

        blueprintEditor = BlueprintEditorWidget(self)
        layout.addWidget(blueprintEditor)
        layout.setStretchFactor(blueprintEditor, 0)

        actionTree = ActionTreeWidget(self)
        layout.addWidget(actionTree)
        layout.setStretchFactor(actionTree, 2)

        actionButtons = ActionButtonsWidget(self)
        layout.addWidget(actionButtons)
        layout.setStretchFactor(actionButtons, 1)

        actionEditor = ActionEditorWidget(self)
        layout.addWidget(actionEditor)
        layout.setStretchFactor(actionEditor, 2)

