import logging
import traceback
from typing import Optional
from ...vendor.Qt import QtCore, QtWidgets

from ...build_items import BuildStep
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
        for validate_result in self.step.get_validate_results():
            label = QtWidgets.QLabel(self)
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
