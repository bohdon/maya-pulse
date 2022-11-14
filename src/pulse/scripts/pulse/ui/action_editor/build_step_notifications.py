import logging
from typing import Optional

from ...vendor.Qt import QtCore, QtWidgets
from ... import names

from ...core import BuildStep
from ..utils import clear_layout

logger = logging.getLogger(__name__)


class BuildStepNotifications(QtWidgets.QWidget):
    """
    Displays the current list of notifications, warnings, and errors for an action.
    """

    def __init__(self, parent=None):
        super(BuildStepNotifications, self).__init__(parent=parent)

        self.step: Optional[BuildStep] = None
        self.setup_ui(self)

    def set_step(self, step):
        self.step = step
        self._refresh()

    def setup_ui(self, parent):
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.layout.setMargin(0)

    def _refresh(self):
        clear_layout(self.layout)

        if not self.step:
            return

        has_notifications = False
        for record in self.step.get_validate_results():
            label = QtWidgets.QLabel(self)
            label.setProperty("cssClasses", "notification error")
            label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
            label.setText(record.getMessage())
            label.setToolTip(self._format_record_tooltip(record))
            self.layout.addWidget(label)
            has_notifications = True

        self.setVisible(has_notifications)

    def _format_record_tooltip(self, record: logging.LogRecord) -> str:
        # build list of results, then combine them
        results = []

        # include action data if it's available
        if hasattr(record, "action_data"):
            results.append(self._format_action_data(record.action_data))

        # add call stack
        if record.exc_text:
            results.append(record.exc_text)

        return "\n\n".join(results)

    def _format_action_data(self, action_data: dict) -> str:
        data_items = action_data.items()
        action_data_msg = "Action Data:\n"
        action_data_lines = [f"    {names.to_title(key)}: {value}" for key, value in data_items]
        action_data_msg += "\n".join(action_data_lines)
        return action_data_msg
