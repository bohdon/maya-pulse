"""
A panel for displaying all actions in a blueprint, adding new actions,
inspecting, and editing actions. Combines ActionEditorWidget, ActionTreeWidget
and ActionPaletteWidget into one widget.
"""


from functools import partial

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets
from pulse.prefs import optionVarProperty

from .core import PulseWindow, BlueprintUIModel
from .actiontree import ActionTreeWidget, ActionPaletteWidget
from .actioneditor import ActionEditorWidget


__all__ = [
    'ActionsViewWidget',
    'ActionsViewWindow',
]


class ActionsViewWidget(QtWidgets.QWidget):
    """
    A panel for displaying all actions in a blueprint, adding new actions,
    inspecting, and editing actions. Combines ActionEditorWidget,
    ActionTreeWidget and ActionPaletteWidgets.
    """

    def __init__(self, parent=None):
        super(ActionsViewWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        self.setupUi(self)
        self.setupMenuBar(self)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        self.setLayout(layout)

        actionsSplitter1 = QtWidgets.QSplitter(parent)
        actionsSplitter1.setOrientation(QtCore.Qt.Orientation.Vertical)

        actionsSplitter2 = QtWidgets.QSplitter(parent)
        actionsSplitter2.setOrientation(QtCore.Qt.Orientation.Horizontal)

        # actions tree
        actionTree = ActionTreeWidget(parent)
        actionTree.layout().setMargin(0)
        actionsSplitter2.addWidget(actionTree)

        # actions palette
        actionPalette = ActionPaletteWidget(parent)
        actionPalette.layout().setMargin(0)
        actionsSplitter2.addWidget(actionPalette)

        actionsSplitter1.addWidget(actionsSplitter2)

        # action editor
        actionEditor = ActionEditorWidget(parent)
        actionEditor.layout().setMargin(0)
        actionsSplitter1.addWidget(actionEditor)

        layout.addWidget(actionsSplitter1)

    def setupMenuBar(self, parent):
        self.menuBar = QtWidgets.QMenuBar(parent)
        self.layout().setMenuBar(self.menuBar)

        actionsMenu = self.menuBar.addMenu("Actions")

        initActions = QtWidgets.QAction("Initialize Default Actions", parent)
        initActions.setStatusTip(
            "Initialize the Blueprint to the default set of actions.")
        initActions.triggered.connect(
            self.blueprintModel.initializeBlueprintToDefaultActions)
        actionsMenu.addAction(initActions)


class ActionsViewWindow(PulseWindow):

    OBJECT_NAME = 'pulseActionsViewWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.actionsview'

    def __init__(self, parent=None):
        super(ActionsViewWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Editor')

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        widget = ActionsViewWidget(self)
        layout.addWidget(widget)
