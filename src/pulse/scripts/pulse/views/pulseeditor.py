
from functools import partial

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets
from pulse.prefs import optionVarProperty

from .core import PulseWindow
from .blueprinteditor import BlueprintEditorWidget
from .buildtoolbar import BuildToolbarWidget
from .actiontree import ActionTreeWidget, ActionPaletteWidget
from .actioneditor import ActionEditorWidget
from .designview import DesignViewWidget


__all__ = [
    'PulseEditorWindow',
]


class PulseEditorWindow(PulseWindow):
    """
    An all-in-one window that contains all pulse editors.
    """

    OBJECT_NAME = 'pulseEditorWindow'
    STARTING_SIZE = QtCore.QSize(400, 600)
    PREFERRED_SIZE = QtCore.QSize(400, 600)
    MINIMUM_SIZE = QtCore.QSize(400, 600)

    WINDOW_MODULE = 'pulse.views.pulseeditor'

    mainTabIndex = optionVarProperty('pulse.editor.mainTabIndex', 0)
    actionsTabIndex = optionVarProperty('pulse.editor.actionsTabIndex', 0)

    def setMainTabIndex(self, index):
        self.mainTabIndex = index

    def setActionsTabIndex(self, index):
        self.actionsTabIndex = index

    def __init__(self, parent=None):
        super(PulseEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse')

        pulse.loadBuiltinActions()

        self.setupUi(self)

        self.mainTabWidget.setCurrentIndex(self.mainTabIndex)
        self.actionsTabWidget.setCurrentIndex(self.actionsTabIndex)

        # connect signals
        self.mainTabWidget.currentChanged.connect(self.setMainTabIndex)
        self.actionsTabWidget.currentChanged.connect(self.setActionsTabIndex)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)
        self.setLayout(layout)

        buildToolbar = BuildToolbarWidget(parent)
        layout.addWidget(buildToolbar)

        # main tab widget (Config / Design / Actions)
        tabWidget = QtWidgets.QTabWidget(parent)

        # config tab
        configTab = BlueprintEditorWidget(parent)
        tabWidget.addTab(configTab, "Config")

        # design tab
        designTab = DesignViewWidget(parent)
        tabWidget.addTab(designTab, "Design")

        # actions tab
        actionsTab = QtWidgets.QWidget(parent)
        actionsLayout = QtWidgets.QVBoxLayout(actionsTab)

        actionsSplitter = QtWidgets.QSplitter(parent)
        actionsSplitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        actionsLayout.addWidget(actionsSplitter)

        actionTree = ActionTreeWidget(actionsTab)
        actionTree.layout().setMargin(0)
        actionsSplitter.addWidget(actionTree)

        # actions tab widget (Palette / Editor)
        actionsTabWidget = QtWidgets.QTabWidget(parent)
        actionsSplitter.addWidget(actionsTabWidget)

        actionPalette = ActionPaletteWidget(actionsTab)
        actionPalette.layout().setMargin(0)
        actionsTabWidget.addTab(actionPalette, "Palette")

        actionEditor = ActionEditorWidget(actionsTab)
        actionEditor.layout().setMargin(0)
        actionsTabWidget.addTab(actionEditor, "Editor")

        tabWidget.addTab(actionsTab, "Actions")

        layout.addWidget(tabWidget)

        self.mainTabWidget = tabWidget
        self.actionsTabWidget = actionsTabWidget
