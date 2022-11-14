import logging

from ..utils import clear_layout
from ...prefs import option_var_property
from ...vendor.Qt import QtCore, QtWidgets

from ..core import BlueprintUIModel
from ..core import PulseWindow
from .build_step_form import BuildStepForm
from ..gen.action_editor import Ui_ActionEditor

logger = logging.getLogger(__name__)


class ActionEditor(QtWidgets.QWidget):
    """
    The main widget for inspecting and editing BuildActions.

    Uses the shared action tree selection model to automatically
    display editors for the selected actions.
    """

    show_descriptions = option_var_property("pulse.editor.actionEditor.showDescriptions", True)

    def set_show_descriptions(self, value):
        if self.show_descriptions != value:
            self.show_descriptions = value
            self.setup_items_ui_for_selection()

    def __init__(self, parent=None):
        super(ActionEditor, self).__init__(parent=parent)

        self.ui = Ui_ActionEditor()
        self.ui.setupUi(self)

        self.blueprint_model = BlueprintUIModel.get_default_model()
        self.model = self.blueprint_model.build_step_tree_model
        self.model.dataChanged.connect(self._on_model_data_changed)
        self.model.modelReset.connect(self._on_model_reset)
        self.selection_model = self.blueprint_model.build_step_selection_model
        self.selection_model.selectionChanged.connect(self._on_selection_changed)

        self.setup_items_ui_for_selection()

    def _on_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        self.setup_items_ui_for_selection()

    def _on_model_data_changed(self):
        # TODO: refresh displayed build step forms if applicable
        pass

    def _on_model_reset(self):
        self.setup_items_ui_for_selection()

    def setup_items_ui(self, item_indexes, parent):
        clear_layout(self.ui.items_layout)

        for index in item_indexes:
            item_widget = BuildStepForm(index, parent=parent)
            self.ui.items_layout.addWidget(item_widget)

    def setup_items_ui_for_selection(self):
        if self.selection_model.hasSelection():
            self.ui.main_stack.setCurrentWidget(self.ui.content_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.help_page)

        self.setup_items_ui(self.selection_model.selectedIndexes(), self.ui.scroll_area_widget)

    def setup_view_menu(self, parent, menu_bar: QtWidgets.QMenuBar):
        view_menu = menu_bar.addMenu("View")

        show_desc_check = QtWidgets.QAction("Show Descriptions", parent)
        show_desc_check.setCheckable(True)
        show_desc_check.setChecked(self.show_descriptions)
        show_desc_check.toggled.connect(self.set_show_descriptions)
        show_desc_check.setStatusTip("Show action descriptions in the editor.")
        view_menu.addAction(show_desc_check)


class ActionEditorWindow(PulseWindow):
    OBJECT_NAME = "pulseActionEditorWindow"
    WINDOW_MODULE = "pulse.ui.action_editor"
    WINDOW_TITLE = "Pulse Action Editor"
    WIDGET_CLASS = ActionEditor

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # setup menu bar
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.layout().setMenuBar(self.menu_bar)

        self.main_widget.setup_view_menu(self, self.menu_bar)
