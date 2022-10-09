"""
The main editor that contains the build toolbar, blueprint settings,
and the list of pulse actions.
"""

from ..vendor.Qt import QtWidgets
from ..prefs import optionVarProperty

import pulse

from .actioneditor import ActionEditorWindow
from .actionpalette import ActionPaletteWindow
from .actionsview import ActionsViewWidget
from .buildtoolbar import BuildToolbarWidget
from .core import PulseWindow, BlueprintUIModel
from .designtoolkit import DesignToolkitWindow
from .manageview import ManageWidget

from .gen.main_editor import Ui_MainEditor

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


class MainEditor(QtWidgets.QWidget):
    """
    The main editor that contains the build toolbar, blueprint settings,
    and the list of pulse actions.
    """

    # the current tab index
    tab_index = optionVarProperty('pulse.editor.mainTabIndex', 0)

    def set_tab_index(self, index):
        self.tab_index = index

    def __init__(self, parent):
        super(MainEditor, self).__init__(parent)

        pulse.loadBuiltinActions()

        self._tab_definitions = TAB_DEFINITIONS
        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        self.ui = Ui_MainEditor()
        self.ui.setupUi(self)
        self.setup_tabs_ui(self)

        # add build toolbar
        self.ui.build_toolbar = BuildToolbarWidget(self)
        self.ui.toolbar_layout.addWidget(self.ui.build_toolbar)

        # setup main menu bar
        self.setup_menu_bar(self)

        # apply current tab index
        self.ui.main_tab_widget.setCurrentIndex(self.tab_index)

        # connect signals
        self.ui.main_tab_widget.currentChanged.connect(self.set_tab_index)

    def setup_tabs_ui(self, parent):
        """
        Create a widget for each tab definition.
        """
        for tabDef in self._tab_definitions:
            widget = tabDef['widgetClass'](parent)
            self.ui.main_tab_widget.addTab(widget, tabDef['name'])

    def setup_menu_bar(self, parent):
        self.menu_bar = QtWidgets.QMenuBar(parent)
        self.layout().setMenuBar(self.menu_bar)

        self.setup_file_menu(parent)
        self.setup_window_menu(parent)

    def setup_file_menu(self, parent):
        fileMenu = self.menu_bar.addMenu("File")

        initBlueprint = QtWidgets.QAction("Initialize", parent)
        initBlueprint.setStatusTip("Delete all actions and reset the Blueprint.")
        initBlueprint.triggered.connect(self.blueprintModel.initializeBlueprint)
        fileMenu.addAction(initBlueprint)

        saveAction = QtWidgets.QAction("Save", parent)
        saveAction.setStatusTip("Save the Blueprint as a yaml file associated with the current maya scene file")
        saveAction.triggered.connect(self.blueprintModel.save)
        fileMenu.addAction(saveAction)

        reloadAction = QtWidgets.QAction("Reload", parent)
        reloadAction.setStatusTip("Reload the Blueprint from the yaml file associated with the current maya scene file")
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
        autosaveCheck.setStatusTip("Automatically save Blueprint files when a scene is saved")
        fileMenu.addAction(autosaveCheck)

        autoloadCheck = QtWidgets.QAction("Auto Load", parent)
        autoloadCheck.setCheckable(True)
        autoloadCheck.setChecked(self.blueprintModel.autoLoad)
        autoloadCheck.toggled.connect(self.blueprintModel.setAutoLoad)
        autoloadCheck.setStatusTip("Automatically load Blueprint files when a scene is opened")
        fileMenu.addAction(autoloadCheck)

    def setup_window_menu(self, parent):
        windowMenu = self.menu_bar.addMenu("Window")

        designToolkit = QtWidgets.QAction("Design Toolkit", parent)
        designToolkit.setStatusTip("Toggle the Design Toolkit window.")
        designToolkit.triggered.connect(DesignToolkitWindow.toggleWindow)
        windowMenu.addAction(designToolkit)

        actionEditor = QtWidgets.QAction("Action Editor", parent)
        actionEditor.setStatusTip("Toggle the Action Editor window.")
        actionEditor.triggered.connect(ActionEditorWindow.toggleWindow)
        windowMenu.addAction(actionEditor)

        actionPalette = QtWidgets.QAction("Action Palette", parent)
        actionPalette.setStatusTip("Toggle the Action Palette window.")
        actionPalette.triggered.connect(ActionPaletteWindow.toggleWindow)
        windowMenu.addAction(actionPalette)

    def debugPrintSerialized(self):
        print(self.blueprintModel, self.blueprintModel.blueprint)
        print(self.blueprintModel.getBlueprintFilepath())
        print(self.blueprintModel.blueprint.dumpYaml())


class PulseEditorWindow(PulseWindow):
    """
    The main editor window that contains the build toolbar, blueprint settings,
    and the list of pulse actions.
    """
    OBJECT_NAME = 'pulseEditorWindow'
    DEFAULT_TAB_CONTROL = "Outliner"
    WINDOW_MODULE = 'pulse.ui.pulseeditor'

    def __init__(self, parent=None):
        super(PulseEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.setLayout(layout)

        widget = MainEditor(self)
        layout.addWidget(widget)
