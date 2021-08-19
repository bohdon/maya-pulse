"""
The main editor window. Contains the build toolbar, and tabs for manage, design,
and actions views.
"""

import pulse
from .actioneditor import ActionEditorWindow
from .actionsview import ActionsViewWidget
from .buildtoolbar import BuildToolbarWidget
from .core import PulseWindow, BlueprintUIModel
from .designview import DesignToolkitWindow
from .manageview import ManageWidget
from ..prefs import optionVarProperty
from ..vendor.Qt import QtCore, QtWidgets

TAB_DEFINITIONS = [
    {
        "name": "Settings",
        "widgetClass": ManageWidget
    },
    {
        "name": "Actions",
        "widgetClass": ActionsViewWidget
    },
]


class PulseEditorWindow(PulseWindow):
    """
    An all-in-one window that contains all pulse editors.
    """

    OBJECT_NAME = 'pulseEditorWindow'
    STARTING_SIZE = QtCore.QSize(400, 600)
    PREFERRED_SIZE = QtCore.QSize(400, 600)
    MINIMUM_SIZE = QtCore.QSize(400, 600)
    DEFAULT_TAB_CONTROL = "Outliner"
    WINDOW_MODULE = 'pulse.views.pulseeditor'

    mainTabIndex = optionVarProperty('pulse.editor.mainTabIndex', 0)

    def setMainTabIndex(self, index):
        self.mainTabIndex = index

    def __init__(self, parent=None):
        super(PulseEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse')
        self.tabDefinitions = TAB_DEFINITIONS

        pulse.loadBuiltinActions()

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        self.setupUi(self)
        self.setupMenuBar(self)

        self.mainTabWidget.setCurrentIndex(self.mainTabIndex)

        # connect signals
        self.mainTabWidget.currentChanged.connect(self.setMainTabIndex)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)
        self.setLayout(layout)

        buildToolbar = BuildToolbarWidget(parent)
        layout.addWidget(buildToolbar)

        tabWidget = QtWidgets.QTabWidget(parent)

        # create a widget for each entry in self.tabDefinitions
        for tabDef in self.tabDefinitions:
            widget = tabDef['widgetClass'](parent)
            tabWidget.addTab(widget, tabDef['name'])

        layout.addWidget(tabWidget)

        self.mainTabWidget = tabWidget

    def setupMenuBar(self, parent):
        self.menuBar = QtWidgets.QMenuBar(parent)
        self.layout().setMenuBar(self.menuBar)

        self.setupFileMenu(parent)
        self.setupWindowMenu(parent)

    def setupFileMenu(self, parent):
        fileMenu = self.menuBar.addMenu("File")

        initBlueprint = QtWidgets.QAction("Initialize", parent)
        initBlueprint.setStatusTip(
            "Delete all actions and reset the Blueprint.")
        initBlueprint.triggered.connect(
            self.blueprintModel.initializeBlueprint)
        fileMenu.addAction(initBlueprint)

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

        debugPrintAction = QtWidgets.QAction("Debug Print YAML", parent)
        debugPrintAction.triggered.connect(self.debugPrintSerialized)
        fileMenu.addAction(debugPrintAction)

        fileMenu.addSeparator()

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

    def setupWindowMenu(self, parent):
        windowMenu = self.menuBar.addMenu("Window")

        toggleDesignToolkit = QtWidgets.QAction("Design Toolkit", parent)
        toggleDesignToolkit.setStatusTip("Toggle the Design Toolkit window.")
        toggleDesignToolkit.triggered.connect(DesignToolkitWindow.toggleWindow)
        windowMenu.addAction(toggleDesignToolkit)

        toggleEditor = QtWidgets.QAction("Action Editor", parent)
        toggleEditor.setStatusTip("Toggle the Action Editor window.")
        toggleEditor.triggered.connect(ActionEditorWindow.toggleWindow)
        windowMenu.addAction(toggleEditor)

    def debugPrintSerialized(self):
        print(self.blueprintModel, self.blueprintModel.blueprint)
        print(self.blueprintModel.getBlueprintFilepath())
        print(self.blueprintModel.blueprint.dumpYaml())
