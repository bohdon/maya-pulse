"""
The main form for editing any build step.
"""

import logging
import traceback
from typing import cast

from .build_action_proxy_form import BuildActionProxyForm
from ... import source_editor
from ...build_items import BuildStep
from ...vendor.Qt import QtCore, QtWidgets, QtGui
from ..core import BuildStepTreeModel

logger = logging.getLogger(__name__)


class BuildStepNotificationsList(QtWidgets.QWidget):
    """
    Displays the current list of notifications, warnings, and errors for an action.
    """

    def __init__(self, step: BuildStep, parent=None):
        super(BuildStepNotificationsList, self).__init__(parent=parent)
        self.setObjectName("formFrame")

        self.step = step

        self.setup_ui(self)

    def setup_ui(self, parent):
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.layout.setMargin(0)

        has_notifications = False
        for validate_result in self.step.get_validate_results():
            label = QtWidgets.QLabel(parent)
            label.setProperty("cssClasses", "notification error")
            label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
            label.setText(str(validate_result))
            label.setToolTip(self.format_error_text(validate_result))
            self.layout.addWidget(label)
            has_notifications = True

        self.setVisible(has_notifications)

    def format_error_text(self, exc: Exception):
        lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        return "".join(lines).strip()


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

        self.setup_ui(self)

        self.index.model().dataChanged.connect(self.on_model_data_changed)

    def on_model_data_changed(self):
        # TODO: refresh displayed values
        if not self.index.isValid():
            self.hide()
            return

        step = self.get_step()
        if not step:
            return

        if self.display_name_label:
            self.display_name_label.setText(self.get_step_display_name(step))

    def get_step(self) -> BuildStep:
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return cast(BuildStepTreeModel, self.index.model()).step_for_index(self.index)

    def get_step_display_name(self, step: BuildStep):
        parent_path = step.get_parent_path()
        if parent_path:
            return f"{step.get_parent_path()}/{step.get_display_name()}".replace("/", " / ")
        else:
            return step.get_display_name()

    def setup_ui(self, parent):
        """
        Create a basic header and body layout to contain the generic
        or action proxy forms.
        """
        step = self.get_step()
        if not step:
            return

        # main layout containing header and body
        self.main_layout = QtWidgets.QVBoxLayout(parent)
        self.main_layout.setSpacing(2)
        self.main_layout.setMargin(0)

        # title / header
        self.setup_header_ui(self)

        # notifications
        notifications = BuildStepNotificationsList(step, parent)
        self.main_layout.addWidget(notifications)

        # body
        self.setup_body_ui(self)
        self.setLayout(self.main_layout)

    def setup_header_ui(self, parent):
        """
        Build the header UI for this build step. Includes the step name and
        a button for quick-editing the action's python script if this step is an action.
        """
        step = self.get_step()
        color = step.get_color()
        color_str = color.as_style()

        bg_color = color * 0.15
        bg_color.a = 0.5
        bg_color_str = bg_color.as_style()

        layout = QtWidgets.QHBoxLayout(parent)
        layout.setMargin(0)

        self.display_name_label = QtWidgets.QLabel(parent)
        self.display_name_label.setText(self.get_step_display_name(step))
        self.display_name_label.setProperty("cssClasses", "section-title")
        self.display_name_label.setStyleSheet(f"color: {color_str}; background-color: {bg_color_str}")
        layout.addWidget(self.display_name_label)

        if step.is_action():
            edit_btn = QtWidgets.QToolButton(parent)
            edit_btn.setIcon(QtGui.QIcon(":/icon/file_pen.svg"))
            edit_btn.setStatusTip("Edit this action's python script.")
            edit_btn.clicked.connect(self._open_action_script_in_source_editor)
            layout.addWidget(edit_btn)

        self.main_layout.addLayout(layout)

    def setup_body_ui(self, parent):
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
            self.main_layout.addWidget(self.action_form)

    def _open_action_script_in_source_editor(self):
        """
        Open the python file for this action in a source editor.
        """
        step = self.get_step()
        if step.is_action() and step.action_proxy.spec:
            source_editor.open_module(step.action_proxy.spec.module)
