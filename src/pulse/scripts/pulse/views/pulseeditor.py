

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets
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

    def __init__(self, parent=None):
        super(PulseEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse')

        pulse.loadBuiltinActions()

        self.setupUi(self)

    def setupUi(self, parent):
        widget = QtWidgets.QWidget(parent)
        widget.setMinimumWidth(300)
        self.setCentralWidget(widget)

        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)
        widget.setLayout(layout)

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
