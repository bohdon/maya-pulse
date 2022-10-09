from .. import utils as viewutils
from ..utils import undoAndRepeatPartial as cmd
from ... import editorutils
from ...vendor.Qt import QtWidgets


class WeightsDesignPanel(QtWidgets.QWidget):

    def __init__(self, parent):
        super(WeightsDesignPanel, self).__init__(parent)

        self.setupUi(self)

    def setupUi(self, parent):
        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        saveWeightsBtn = QtWidgets.QPushButton(parent)
        saveWeightsBtn.setText("Save Skin Weights")
        saveWeightsBtn.setStatusTip(
            "Save all skin weights in the scene a weights file")
        saveWeightsBtn.clicked.connect(cmd(editorutils.saveAllSkinWeights))

        gridItems = [
            [saveWeightsBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)
