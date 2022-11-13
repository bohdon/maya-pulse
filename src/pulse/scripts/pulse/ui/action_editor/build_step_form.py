"""
The main form for editing any build step.
"""

import logging
from typing import cast
from ...vendor.Qt import QtCore, QtWidgets

from ... import source_editor
from ...build_items import BuildStep
from ...colors import LinearColor
from ..core import BuildStepTreeModel
from .build_action_proxy_form import BuildActionProxyForm
from ..gen.build_step_form import Ui_BuildStepForm

logger = logging.getLogger(__name__)


class BuildStepForm(QtWidgets.QWidget):
    """
    A form for editing a BuildStep
    """

    def __init__(self, index: QtCore.QModelIndex, parent=None):
        """
        Args:
            index (QModelIndex): The index of the BuildStep
        """
        super(BuildStepForm, self).__init__(parent=parent)
        self.display_name_label = None
        self.action_form = None

        self.index = QtCore.QPersistentModelIndex(index)
        step = self.get_step()

        self.ui = Ui_BuildStepForm()
        self.ui.setupUi(self)
        self.ui.notifications.set_step(step)
        self.setup_content_ui(self, step)

        # set title text and color
        self.ui.display_name_label.setText(self._get_step_display_name(step))
        self._apply_title_color(step.get_color())

        # show edit source button for actions
        self.ui.edit_source_btn.clicked.connect(self._open_action_script_in_source_editor)

        self.index.model().dataChanged.connect(self.on_model_data_changed)

    def _apply_title_color(self, color: LinearColor):
        color_str = color.as_style()

        bg_color = color * 0.15
        bg_color.a = 0.5
        bg_color_str = bg_color.as_style()

        self.ui.display_name_label.setStyleSheet(f"color: {color_str}; background-color: {bg_color_str}")

    def on_model_data_changed(self):
        # TODO: refresh displayed values
        if not self.index.isValid():
            self.hide()
            return

        step = self.get_step()
        if not step:
            return

        if self.display_name_label:
            self.display_name_label.setText(self._get_step_display_name(step))

    def get_step(self) -> BuildStep:
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return cast(BuildStepTreeModel, self.index.model()).step_for_index(self.index)

    def _get_step_display_name(self, step: BuildStep):
        parent_path = step.get_parent_path()
        if parent_path:
            return f"{step.get_parent_path()}/{step.get_display_name()}".replace("/", " / ")
        else:
            return step.get_display_name()

    def setup_content_ui(self, parent, step):
        """
        Build the body UI for this build step.

        If this step is an action, create a BuildActionProxyForm widget, possibly using the custom
        `editor_form_cls` defined on the action.
        """
        step = self.get_step()
        if step.is_action() and step.action_proxy.is_valid():
            custom_form_cls = step.action_proxy.spec.editor_form_cls
            if not custom_form_cls:
                # use default form
                custom_form_cls = BuildActionProxyForm
            self.action_form = custom_form_cls(self.index, parent)
            self.layout().addWidget(self.action_form)

    def _open_action_script_in_source_editor(self):
        """
        Open the python file for this action in a source editor.
        """
        step = self.get_step()
        if step.is_action() and step.action_proxy.spec:
            source_editor.open_module(step.action_proxy.spec.module)
