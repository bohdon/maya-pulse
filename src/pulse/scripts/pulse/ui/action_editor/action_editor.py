import logging

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

    def __init__(self, parent=None):
        super(ActionEditor, self).__init__(parent=parent)

        self.ui = Ui_ActionEditor()
        self.ui.setupUi(self)

        self.blueprintModel = BlueprintUIModel.get_default_model()
        self.blueprintModel.read_only_changed.connect(self.on_read_only_changed)
        self.model = self.blueprintModel.build_step_tree_model
        self.model.dataChanged.connect(self.on_model_data_changed)
        self.model.modelReset.connect(self.on_model_reset)
        self.selectionModel = self.blueprintModel.build_step_selection_model
        self.selectionModel.selectionChanged.connect(self._on_selection_changed)

        self.setEnabled(not self.blueprintModel.is_read_only())

        self.setup_items_ui_for_selection()

    def _on_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        self.setup_items_ui_for_selection()

    def on_model_data_changed(self):
        # TODO: refresh displayed build step forms if applicable
        pass

    def on_model_reset(self):
        self.setup_items_ui_for_selection()

    def on_read_only_changed(self, is_read_only):
        self.setEnabled(not is_read_only)

    def clear_items_ui(self):
        while True:
            item = self.ui.items_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
            else:
                break

    def setup_items_ui(self, item_indexes, parent):
        self.clear_items_ui()

        for index in item_indexes:
            item_widget = BuildStepForm(index, parent=parent)
            self.ui.items_layout.addWidget(item_widget)

    def setup_items_ui_for_selection(self):
        if self.selectionModel.hasSelection():
            self.ui.main_stack.setCurrentWidget(self.ui.content_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.help_page)

        self.setup_items_ui(self.selectionModel.selectedIndexes(), self.ui.scroll_area_widget)


class ActionEditorWindow(PulseWindow):
    OBJECT_NAME = "pulseActionEditorWindow"
    WINDOW_MODULE = "pulse.ui.action_editor"
    WINDOW_TITLE = "Pulse Action Editor"
    WIDGET_CLASS = ActionEditor
