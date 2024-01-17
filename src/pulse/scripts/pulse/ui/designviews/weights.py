from PySide2 import QtWidgets

from ..gen.designpanel_weights import Ui_WeightsDesignPanel
from ..utils import undo_and_repeat_partial as cmd
from ... import editor_utils


class WeightsDesignPanel(QtWidgets.QWidget):
    def __init__(self, parent):
        super(WeightsDesignPanel, self).__init__(parent)

        self.ui = Ui_WeightsDesignPanel()
        self.ui.setupUi(self)

        self.ui.save_weights_btn.clicked.connect(cmd(editor_utils.save_all_skin_weights))
