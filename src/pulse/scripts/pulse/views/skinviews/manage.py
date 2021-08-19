from .. import utils as viewutils
from ..core import PulsePanelWidget
from ..utils import undoAndRepeatPartial as cmd
from ... import editorutils
from ...vendor.Qt import QtWidgets


class ManageWeightsPanel(PulsePanelWidget):

    def __init__(self, parent):
        super(ManageWeightsPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "Manage"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        gridLayout = QtWidgets.QGridLayout(frame)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        saveWeightsBtn = QtWidgets.QPushButton(frame)
        saveWeightsBtn.setText("Save Skin Weights")
        saveWeightsBtn.setStatusTip(
            "Save all skin weights in the scene a weights file")
        saveWeightsBtn.clicked.connect(cmd(editorutils.saveAllSkinWeights))

        gridItems = [
            [saveWeightsBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)
