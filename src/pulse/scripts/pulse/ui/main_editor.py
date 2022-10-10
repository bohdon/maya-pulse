"""
The main editor that contains the build toolbar, blueprint settings,
and the list of pulse actions.
"""
from ..vendor.Qt import QtCore, QtWidgets

import pulse

from .actioneditor import ActionEditorWindow
from .actiontree import ActionTree, ActionTreeWindow
from .actionpalette import ActionPaletteWindow
from .main_toolbar import MainToolbar
from .core import PulseWindow, BlueprintUIModel
from .designtoolkit import DesignToolkitWindow

from .gen.main_editor import Ui_MainEditor


class MainEditor(QtWidgets.QWidget):
    """
    The main editor that contains the build toolbar, the main pulse menu bar, and an Action Tree.
    Also contains a toolbar for quickly accessing settings, design toolkit, and action editor.
    """

    def __init__(self, parent):
        super(MainEditor, self).__init__(parent)

        pulse.loadBuiltinActions()

        self.blueprint_model = BlueprintUIModel.getDefaultModel()
        self.selection_model = self.blueprint_model.buildStepSelectionModel
        self.selection_model.selectionChanged.connect(self._on_action_selection_changed)

        self.ui = Ui_MainEditor()
        self.ui.setupUi(self)

        # add build toolbar
        self.ui.build_toolbar = MainToolbar(self)
        self.ui.toolbar_layout.addWidget(self.ui.build_toolbar)

        # add action tree
        self.action_tree_widget = ActionTree(self)
        self.ui.action_tree_layout.addWidget(self.action_tree_widget)

    def setup_file_menu(self, parent, menu_bar):
        file_menu = menu_bar.addMenu("File")

        init_blueprint = QtWidgets.QAction("Initialize", parent)
        init_blueprint.setStatusTip("Delete all actions and reset the Blueprint.")
        init_blueprint.triggered.connect(self.blueprint_model.initializeBlueprint)
        file_menu.addAction(init_blueprint)

        save_action = QtWidgets.QAction("Save", parent)
        save_action.setStatusTip("Save the Blueprint as a yaml file associated with the current maya scene file")
        save_action.triggered.connect(self.blueprint_model.save)
        file_menu.addAction(save_action)

        reload_action = QtWidgets.QAction("Reload", parent)
        reload_action.setStatusTip(
            "Reload the Blueprint from the yaml file associated with the current maya scene file")
        reload_action.triggered.connect(self.blueprint_model.load)
        file_menu.addAction(reload_action)

        file_menu.addSeparator()

        debug_print_action = QtWidgets.QAction("Debug Print YAML", parent)
        debug_print_action.triggered.connect(self.debug_print_serialized)
        file_menu.addAction(debug_print_action)

        file_menu.addSeparator()

        autosave_check = QtWidgets.QAction("Auto Save", parent)
        autosave_check.setCheckable(True)
        autosave_check.setChecked(self.blueprint_model.auto_save)
        autosave_check.toggled.connect(self.blueprint_model.set_auto_save)
        autosave_check.setStatusTip("Automatically save Blueprint files when a scene is saved")
        file_menu.addAction(autosave_check)

        autoload_check = QtWidgets.QAction("Auto Load", parent)
        autoload_check.setCheckable(True)
        autoload_check.setChecked(self.blueprint_model.auto_load)
        autoload_check.toggled.connect(self.blueprint_model.set_auto_load)
        autoload_check.setStatusTip("Automatically load Blueprint files when a scene is opened")
        file_menu.addAction(autoload_check)

    def setup_window_menu(self, parent, menu_bar):
        window_menu = menu_bar.addMenu("Window")

        design_toolkit = QtWidgets.QAction("Design Toolkit", parent)
        design_toolkit.setStatusTip("Toggle the Design Toolkit window.")
        design_toolkit.triggered.connect(DesignToolkitWindow.toggleWindow)
        window_menu.addAction(design_toolkit)

        action_editor = QtWidgets.QAction("Action Editor", parent)
        action_editor.setStatusTip("Toggle the Action Editor window.")
        action_editor.triggered.connect(ActionEditorWindow.toggleWindow)
        window_menu.addAction(action_editor)

        action_palette = QtWidgets.QAction("Action Palette", parent)
        action_palette.setStatusTip("Toggle the Action Palette window.")
        action_palette.triggered.connect(ActionPaletteWindow.toggleWindow)
        window_menu.addAction(action_palette)

        action_tree = QtWidgets.QAction("Action Tree", parent)
        action_tree.setStatusTip("Toggle a standalone Action Tree window.")
        action_tree.triggered.connect(ActionTreeWindow.toggleWindow)
        window_menu.addAction(action_tree)

        window_menu.addSeparator()

        auto_show_editor = QtWidgets.QAction("Auto Focus Action Editor", parent)
        auto_show_editor.setCheckable(True)
        auto_show_editor.setChecked(self.blueprint_model.auto_show_action_editor)
        auto_show_editor.toggled.connect(self.blueprint_model.set_auto_show_action_editor)
        auto_show_editor.setStatusTip("Automatically show the Action Editor when selecting an Action in the tree.")
        window_menu.addAction(auto_show_editor)

    def setup_actions_menu(self, parent, menu_bar):
        self.action_tree_widget.setup_actions_menu(parent, menu_bar)

    def debug_print_serialized(self):
        print(self.blueprint_model, self.blueprint_model.blueprint)
        print(self.blueprint_model.getBlueprintFilepath())
        print(self.blueprint_model.blueprint.dumpYaml())

    def _on_action_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        if not selected.isEmpty():
            if self.blueprint_model.auto_show_action_editor:
                ActionEditorWindow.showWindow()


class MainEditorWindow(PulseWindow):
    """
    The main editor window that contains the build toolbar, blueprint settings,
    and the list of pulse actions.
    """
    OBJECT_NAME = 'pulseMainEditorWindow'
    WINDOW_MODULE = 'pulse.ui.main_editor'
    WINDOW_TITLE = 'Pulse'
    WIDGET_CLASS = MainEditor

    def __init__(self, parent=None):
        super(MainEditorWindow, self).__init__(parent)

        # setup menu bar
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.layout().setMenuBar(self.menu_bar)

        self.main_widget.setup_file_menu(self, self.menu_bar)
        self.main_widget.setup_window_menu(self, self.menu_bar)
        self.main_widget.setup_actions_menu(self, self.menu_bar)
