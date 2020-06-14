
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm

from pulse.views import utils as viewutils
from pulse.views.utils import undoAndRepeatPartial as cmd
from pulse.views.core import PulseWindow, PulsePanelWidget
from pulse import editorutils
from pulse import links

__all__ = [
    "LayoutLinkEditorWidget",
    "LayoutLinkEditorWindow",
    "LayoutPanel",
]


class LayoutPanel(PulsePanelWidget):

    def __init__(self, parent):
        super(LayoutPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "Layout"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        gridLayout = QtWidgets.QGridLayout(frame)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        snapToTargetsBtn = QtWidgets.QPushButton(frame)
        snapToTargetsBtn.setText("Snap To Targets")
        snapToTargetsBtn.setStatusTip(
            "Snap controls and linked objects to their target positions")
        snapToTargetsBtn.clicked.connect(
            cmd(editorutils.positionLinkForSelected))

        linkEditorBtn = QtWidgets.QPushButton(frame)
        linkEditorBtn.setText("Link Editor")
        linkEditorBtn.setStatusTip(
            "Open the Layout Link Editor for managing how nodes are connected "
            "to each other during blueprint design")
        linkEditorBtn.clicked.connect(
            cmd(LayoutLinkEditorWindow.toggleWindow))

        gridItems = [
            [snapToTargetsBtn, linkEditorBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)


class LayoutLinkEditorWidget(QtWidgets.QWidget):

    def __init__(self, parent):
        super(LayoutLinkEditorWidget, self).__init__(parent=parent)
        self.setupUi(self)

    def setupUi(self, parent):
        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)
        self.setLayout(gridLayout)

        linkDefaultBtn = QtWidgets.QPushButton(parent)
        linkDefaultBtn.setText("Link")
        linkDefaultBtn.clicked.connect(
            cmd(editorutils.linkSelected, linkType=links.LinkType.DEFAULT))

        linkIkPoleBtn = QtWidgets.QPushButton(parent)
        linkIkPoleBtn.setText("Link IK Pole")
        linkIkPoleBtn.clicked.connect(
            cmd(editorutils.linkSelected, linkType=links.LinkType.IKPOLE))

        unlinkBtn = QtWidgets.QPushButton(parent)
        unlinkBtn.setText("Unlink")
        unlinkBtn.clicked.connect(
            cmd(editorutils.unlinkSelected))

        gridItems = [
            [linkDefaultBtn, linkIkPoleBtn],
            [unlinkBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)


class LayoutLinkEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseLayoutLinkEditorWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.designviews.layout'

    def __init__(self, parent=None):
        super(LayoutLinkEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Layout Link Editor')
        self.setMinimumSize(300, 100)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(10)
        self.setLayout(layout)

        widget = LayoutLinkEditorWidget(self)
        layout.addWidget(widget)

    def onSelectionChanged(self):
        pass
