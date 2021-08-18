"""
A panel for displaying all actions in a blueprint, adding new actions,
inspecting, and editing actions. Combines ActionEditorWidget, ActionTreeWidget
and ActionPaletteWidget into one widget.
"""

from pulse.vendor.Qt import QtCore, QtWidgets
from .actioneditor import ActionEditorWidget
from .actiontree import ActionTreeWidget, ActionPaletteWidget
from .core import PulseWindow, BlueprintUIModel

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

        # actions tree
        actionTree = ActionTreeWidget(parent)
        actionTree.layout().setMargin(0)
        layout.addWidget(actionTree)

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
