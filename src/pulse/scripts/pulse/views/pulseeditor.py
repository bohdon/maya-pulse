
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse
from .core import PulseWindow
from .blueprinteditor import BlueprintEditorWidget
from .buildtoolbar import BuildToolbarWidget
from .actiontree import ActionTreeWidget
from .actiontree import ActionButtonsWidget
from .actioneditor import ActionEditorWidget


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

        self.setupUi(self)
    
    def setupUi(self, parent):
        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)

        layout = QtWidgets.QVBoxLayout(self)
        widget.setLayout(layout)

        buildToolbar = BuildToolbarWidget(self)
        layout.addWidget(buildToolbar)

        tabWidget = QtWidgets.QTabWidget(self)


        # config tab
        configTab = QtWidgets.QWidget(self)
        configLayout = QtWidgets.QVBoxLayout(configTab)

        blueprintEditor = BlueprintEditorWidget(self)
        configLayout.addWidget(blueprintEditor)

        tabWidget.addTab(configTab, "Config")


        # design tab
        designTab = QtWidgets.QWidget(self)

        tabWidget.addTab(designTab, "Design")
        

        # actions tab
        actionsTab = QtWidgets.QWidget(self)
        actionsLayout = QtWidgets.QVBoxLayout(actionsTab)

        actionTree = ActionTreeWidget(self)
        actionsLayout.addWidget(actionTree)
        actionsLayout.setStretchFactor(actionTree, 2)

        actionButtons = ActionButtonsWidget(self)
        actionsLayout.addWidget(actionButtons)
        actionsLayout.setStretchFactor(actionButtons, 1)

        actionEditor = ActionEditorWidget(self)
        actionsLayout.addWidget(actionEditor)
        actionsLayout.setStretchFactor(actionEditor, 2)

        tabWidget.addTab(actionsTab, "Actions")


        layout.addWidget(tabWidget)
