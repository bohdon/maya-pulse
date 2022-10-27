from ... import editorutils
from ...vendor.Qt import QtWidgets
from ..utils import undoAndRepeatPartial as cmd

from ..gen.designpanel_weights import Ui_WeightsDesignPanel


class WeightsDesignPanel(QtWidgets.QWidget):

    def __init__(self, parent):
        super(WeightsDesignPanel, self).__init__(parent)

        self.ui = Ui_WeightsDesignPanel()
        self.ui.setupUi(self)

        self.ui.save_weights_btn.clicked.connect(cmd(editorutils.save_all_skin_weights))
