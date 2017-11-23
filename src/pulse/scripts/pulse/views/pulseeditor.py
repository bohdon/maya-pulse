
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse
from .core import PulseWindow
from .blueprinteditor import BlueprintEditorWidget
from .buildtoolbar import BuildToolbarWidget
from .actiontree import ActionTreeItemModel, ActionTreeWidget, ActionButtonsWidget
from .actioneditor import ActionEditorWidget, ActionEditorWindow


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
        widget.setMinimumWidth(280)
        self.setCentralWidget(widget)

        layout = QtWidgets.QVBoxLayout(parent)
        widget.setLayout(layout)

        buildToolbar = BuildToolbarWidget(parent)
        layout.addWidget(buildToolbar)

        tabWidget = QtWidgets.QTabWidget(parent)


        # config tab
        configTab = QtWidgets.QWidget(parent)
        configLayout = QtWidgets.QVBoxLayout(configTab)

        blueprintEditor = BlueprintEditorWidget(configTab)
        blueprintEditor.layout().setMargin(0)
        configLayout.addWidget(blueprintEditor)

        tabWidget.addTab(configTab, "Config")


        # design tab
        designTab = QtWidgets.QWidget(parent)

        tabWidget.addTab(designTab, "Design")
        

        # actions tab
        actionsTab = QtWidgets.QWidget(parent)
        actionsLayout = QtWidgets.QVBoxLayout(actionsTab)

        actionEditorBtn = QtWidgets.QPushButton(actionsTab)
        actionEditorBtn.setText("Action Editor")
        actionEditorBtn.clicked.connect(self.showActionEditor)
        actionsLayout.addWidget(actionEditorBtn)

        actionTree = ActionTreeWidget(actionsTab)
        actionTree.layout().setMargin(0)
        actionsLayout.addWidget(actionTree)

        actionButtons = ActionButtonsWidget(actionsTab)
        actionButtons.layout().setMargin(0)
        actionsLayout.addWidget(actionButtons)

        tabWidget.addTab(actionsTab, "Actions")


        layout.addWidget(tabWidget)

        # debug controls
        refreshBtn = QtWidgets.QPushButton(parent)
        refreshBtn.setText('Refresh')
        model = ActionTreeItemModel.getSharedModel()
        refreshBtn.clicked.connect(model.reloadBlueprint)
        layout.addWidget(refreshBtn)
    
    def showActionEditor(self):
        ActionEditorWindow.createAndShow()
