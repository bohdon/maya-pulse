"""
Palette for browsing actions that can be added to a blueprint.
"""

import logging
import os
from functools import partial

from PySide2 import QtWidgets

from .core import BlueprintUIModel, PulseWindow
from .gen.action_palette import Ui_ActionPalette
from ..colors import LinearColor
from ..core import BuildActionRegistry

LOG = logging.getLogger(__name__)
LOG_LEVEL_KEY = "PYLOG_%s" % LOG.name.split(".")[0].upper()
LOG.setLevel(os.environ.get(LOG_LEVEL_KEY, "INFO").upper())


class ActionPalette(QtWidgets.QWidget):
    """
    Provides UI for creating any BuildAction. One button is created
    for each BuildAction, and they are grouped by category. Also
    includes a search field for filtering the list of actions.
    """

    def __init__(self, parent=None):
        super(ActionPalette, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.get_default_model()
        self.blueprintModel.read_only_changed.connect(self._on_read_only_changed)
        self.model = self.blueprintModel.build_step_tree_model
        self.selectionModel = self.blueprintModel.build_step_selection_model

        self.ui = Ui_ActionPalette()
        self.ui.setupUi(self)

        self.setup_actions_ui(self.ui.scroll_area_widget, self.ui.actions_layout)

        self.ui.group_btn.clicked.connect(self.blueprintModel.create_group)

        self._on_read_only_changed(self.blueprintModel.is_read_only())

    def setup_actions_ui(self, parent, layout):
        """
        Build buttons for creating each action.
        """

        all_action_specs = BuildActionRegistry.get().get_all_actions()

        # make button for each action
        categories = [spec.category for spec in all_action_specs]
        categories = list(set(categories))
        category_layouts = {}

        # create category layouts
        for cat in sorted(categories):
            # add category layout
            cat_lay = QtWidgets.QVBoxLayout(parent)
            cat_lay.setSpacing(2)
            layout.addLayout(cat_lay)
            category_layouts[cat] = cat_lay
            # add label
            label = QtWidgets.QLabel(parent)
            label.setText(cat)
            label.setProperty("cssClasses", "section-title")
            cat_lay.addWidget(label)

        for actionSpec in all_action_specs:
            action_id = actionSpec.id
            action_category = actionSpec.category
            color = LinearColor.from_seq(actionSpec.color)
            color.a = 0.12
            btn = QtWidgets.QPushButton(parent)
            btn.setText(actionSpec.display_name)
            btn.setStyleSheet(color.as_bg_style())
            btn.clicked.connect(partial(self.blueprintModel.create_action, action_id))
            category_layouts[action_category].addWidget(btn)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        layout.addItem(spacer)

    def _on_read_only_changed(self, is_read_only):
        self.ui.group_btn.setEnabled(not is_read_only)
        self.ui.scroll_area_widget.setEnabled(not is_read_only)

    def _on_action_clicked(self, type_name):
        self.clicked.emit(type_name)


class ActionPaletteWindow(PulseWindow):
    OBJECT_NAME = "pulseActionPaletteWindow"
    WINDOW_MODULE = "pulse.ui.actionpalette"
    WINDOW_TITLE = "Pulse Action Palette"
    WIDGET_CLASS = ActionPalette
