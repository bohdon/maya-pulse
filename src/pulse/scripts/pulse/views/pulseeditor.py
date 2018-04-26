

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets
from .core import PulseWindow
from .blueprinteditor import BlueprintEditorWidget
from .buildtoolbar import BuildToolbarWidget
from .actiontree import ActionTreeWidget, ActionButtonsWidget
from .actioneditor import ActionEditorWindow
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

        actionEditorBtn = QtWidgets.QPushButton(actionsTab)
        actionEditorBtn.setText("Action Editor")
        actionEditorBtn.clicked.connect(self.showActionEditor)
        actionsLayout.addWidget(actionEditorBtn)

        actionsSplitter = QtWidgets.QSplitter(parent)
        actionsSplitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        actionsLayout.addWidget(actionsSplitter)

        actionTree = ActionTreeWidget(actionsTab)
        actionTree.layout().setMargin(0)
        actionsSplitter.addWidget(actionTree)

        actionButtons = ActionButtonsWidget(actionsTab)
        actionButtons.layout().setMargin(0)
        actionsSplitter.addWidget(actionButtons)

        tabWidget.addTab(actionsTab, "Actions")


        layout.addWidget(tabWidget)

    def showActionEditor(self):
        ActionEditorWindow.createAndShow()
