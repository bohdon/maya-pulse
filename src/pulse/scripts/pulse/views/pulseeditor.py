"""
The main editor window. Contains the build toolbar, and tabs for manage, design,
and actions views.
"""


from functools import partial

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets
from pulse.prefs import optionVarProperty

from .core import PulseWindow, BlueprintUIModel
from .manageview import ManageWidget
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

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        self.setupUi(self)
        self.setupMenuBar(self)

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

        # main tab widget (Manage / Design / Actions)
        tabWidget = QtWidgets.QTabWidget(parent)

        # manage tab
        manageTab = ManageWidget(parent)
        tabWidget.addTab(manageTab, "Manage")

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

    def setupMenuBar(self, parent):
        self.menuBar = QtWidgets.QMenuBar(parent)
        self.layout().setMenuBar(self.menuBar)

        fileMenu = self.menuBar.addMenu("Blueprint")

        autosaveCheck = QtWidgets.QAction("Auto Save", parent)
        autosaveCheck.setCheckable(True)
        autosaveCheck.setChecked(self.blueprintModel.autoSave)
        autosaveCheck.toggled.connect(self.blueprintModel.setAutoSave)
        autosaveCheck.setStatusTip(
            "Automatically save Blueprint files when a scene is saved")
        fileMenu.addAction(autosaveCheck)

        autoloadCheck = QtWidgets.QAction("Auto Load", parent)
        autoloadCheck.setCheckable(True)
        autoloadCheck.setChecked(self.blueprintModel.autoLoad)
        autoloadCheck.toggled.connect(self.blueprintModel.setAutoLoad)
        autoloadCheck.setStatusTip(
            "Automatically load Blueprint files when a scene is opened")
        fileMenu.addAction(autoloadCheck)

        saveAction = QtWidgets.QAction("Save", parent)
        saveAction.setStatusTip(
            "Save the Blueprint as a yaml file associated with the current maya scene file")
        saveAction.triggered.connect(self.blueprintModel.save)
        fileMenu.addAction(saveAction)

        reloadAction = QtWidgets.QAction("Reload", parent)
        reloadAction.setStatusTip(
            "Reload the Blueprint from the yaml file associated with the current maya scene file")
        reloadAction.triggered.connect(self.blueprintModel.load)
        fileMenu.addAction(reloadAction)

        fileMenu.addSeparator()

        reloadAction = QtWidgets.QAction("Clear", parent)
        reloadAction.setStatusTip(
            "Delete all actions and reset the Blueprint.")
        reloadAction.triggered.connect(
            self.blueprintModel.initializeBlueprint)
        fileMenu.addAction(reloadAction)

        reloadAction = QtWidgets.QAction("Create Default Actions", parent)
        reloadAction.setStatusTip(
            "Reset the Blueprint to the default set of actions.")
        reloadAction.triggered.connect(
            self.blueprintModel.initializeBlueprintToDefaultActions)
        fileMenu.addAction(reloadAction)

        fileMenu.addSeparator()

        debugPrintAction = QtWidgets.QAction("Debug Print YAML", parent)
        debugPrintAction.triggered.connect(self.debugPrintSerialized)
        fileMenu.addAction(debugPrintAction)

    def debugPrintSerialized(self):
        print(self.blueprintModel, self.blueprintModel.blueprint)
        print(self.blueprintModel.getBlueprintFilepath())
        print(self.blueprintModel.blueprint.dumpYaml())
