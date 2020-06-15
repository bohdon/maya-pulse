
from maya import OpenMaya as api

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

        self.linkInfoScrollArea = None
        self.linkInfoList = None

        self.setupUi(self)

        self.selection_changed_cb = None

    def showEvent(self, event):
        super(LayoutLinkEditorWidget, self).showEvent(event)
        if self.selection_changed_cb is None:
            print('adding selection changed callback')
            self.selection_changed_cb = api.MEventMessage.addEventCallback("SelectionChanged", self.onSceneSelectionChanged)
        self.updateLinkInfoList()

    def hideEvent(self, event):
        super(LayoutLinkEditorWidget, self).hideEvent(event)
        if self.selection_changed_cb is not None:
            print('removing selection changed callback')
            api.MMessage.removeCallback(self.selection_changed_cb)
            self.selection_changed_cb = None

    def onSceneSelectionChanged(self, *args, **kwargs):
        self.updateLinkInfoList()

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)
        layout.setSpacing(2)

        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)
        layout.addLayout(gridLayout)

        linkDefaultBtn = QtWidgets.QPushButton(parent)
        linkDefaultBtn.setText("Link")
        linkDefaultBtn.clicked.connect(
            cmd(self.linkSelected, linkType=links.LinkType.DEFAULT))

        linkIkPoleBtn = QtWidgets.QPushButton(parent)
        linkIkPoleBtn.setText("Link IK Pole")
        linkIkPoleBtn.clicked.connect(
            cmd(self.linkSelected, linkType=links.LinkType.IKPOLE))

        saveOffsetBtn = QtWidgets.QPushButton(parent)
        saveOffsetBtn.setText("Save Offsets")
        saveOffsetBtn.clicked.connect(
            cmd(self.saveLinkOffsetsForSelected))

        clearOffsetBtn = QtWidgets.QPushButton(parent)
        clearOffsetBtn.setText("Clear Offsets")
        clearOffsetBtn.clicked.connect(
            cmd(self.clearLinkOffsetsForSelected))

        gridItems = [
            [linkDefaultBtn, linkIkPoleBtn],
            [saveOffsetBtn, clearOffsetBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)

        unlinkBtn = QtWidgets.QPushButton(parent)
        unlinkBtn.setText("Unlink")
        unlinkBtn.clicked.connect(
            cmd(self.unlinkSelected))
        layout.addWidget(unlinkBtn)

        snapBtn = QtWidgets.QPushButton(parent)
        snapBtn.setText("Snap to Targets")
        snapBtn.clicked.connect(
            cmd(editorutils.positionLinkForSelected))
        layout.addWidget(snapBtn)

        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(spacer)

        linkInfoLabel = self.createSectionLabel(parent, "Links", True)
        layout.addWidget(linkInfoLabel)

        self.linkInfoScrollArea = QtWidgets.QScrollArea(parent)
        self.linkInfoScrollArea.setFrameShape(QtWidgets.QScrollArea.NoFrame)
        self.linkInfoScrollArea.setWidgetResizable(True)
        layout.addWidget(self.linkInfoScrollArea)

        refreshBtn = QtWidgets.QPushButton(parent)
        refreshBtn.setText("Refresh")
        refreshBtn.setToolTip("Show the link data for the selected nodes")
        refreshBtn.clicked.connect(self.updateLinkInfoList)
        layout.addWidget(refreshBtn)

        self.setLayout(layout)

    def createSectionLabel(self, parent, text, bold=False):
        label = QtWidgets.QLabel(parent)
        label.setText(text)
        if bold:
            font = QtGui.QFont()
            font.setWeight(75)
            font.setBold(True)
            label.setFont(font)
        label.setMinimumHeight(20)
        label.setContentsMargins(10, 2, 2, 2)
        label.setStyleSheet(
            'background-color: rgba(0, 0, 0, 40); border-radius: 2px')
        return label

    def updateLinkInfoList(self):
        if self.linkInfoList:
            self.linkInfoList.deleteLater()
            self.linkInfoList = None

        # get selected nodes and link data
        selNodes = pm.selected()
        self.linkInfoList = LinkInfoListWidget(self, selNodes)
        self.linkInfoScrollArea.setWidget(self.linkInfoList)

    def linkSelected(self, linkType):
        editorutils.linkSelected(linkType=linkType)
        self.updateLinkInfoList()

    def saveLinkOffsetsForSelected(self):
        editorutils.saveLinkOffsetsForSelected()
        self.updateLinkInfoList()

    def clearLinkOffsetsForSelected(self):
        editorutils.clearLinkOffsetsForSelected()
        self.updateLinkInfoList()

    def unlinkSelected(self):
        editorutils.unlinkSelected()
        self.updateLinkInfoList()


class LinkInfoListWidget(QtWidgets.QWidget):
    """
    Displays info for a list of linked nodes
    """

    def __init__(self, parent, nodes):
        super(LinkInfoListWidget, self).__init__(parent=parent)

        self.nodes = [n for n in nodes if n]

        self.setupUi(self)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(4)

        for node in self.nodes:
            if not links.isLinked(node):
                continue
            linkData = links.getLinkMetaData(node)
            linkInfo = LinkInfoWidget(parent, node, linkData)
            layout.addWidget(linkInfo)

        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

        self.setLayout(layout)


class LinkInfoWidget(QtWidgets.QWidget):
    """
    Displays info about a linked node
    """

    def __init__(self, parent, node, linkData):
        super(LinkInfoWidget, self).__init__(parent=parent)

        if not node:
            raise ValueError("Node must be a valid PyNode")
        self.node = node
        self.linkData = linkData

        self.setupUi(self)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        # add node name label
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        nodeNameLabel = QtWidgets.QLabel(parent)
        nodeNameLabel.setFont(font)
        nodeNameLabel.setText(self.node.name())
        layout.addWidget(nodeNameLabel)

        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setContentsMargins(20, 0, 0, 0)
        gridLayout.setSpacing(2)
        layout.addLayout(gridLayout)
        gridItems = []

        # get link data keys, sorted with `targetNode` and `type` first
        keys = ['targetNode', 'type']
        keys += [k for k in self.linkData.keys() if k not in keys]

        # create labels for each piece of data
        for key in keys:
            value = self.linkData.get(key)
            if not value:
                if key == 'targetNode':
                    value = '(missing)'
                elif key == 'type':
                    value = links.LinkType.DEFAULT

            nameLabel = QtWidgets.QLabel(parent)
            nameLabel.setText(key)
            valueLabel = QtWidgets.QLabel(parent)
            valueLabel.setText(str(value))

            # add new items to list of pending grid items
            gridItems.append([nameLabel, valueLabel])

        viewutils.addItemsToGrid(gridLayout, gridItems)

        self.setLayout(layout)


class LayoutLinkEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseLayoutLinkEditorWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.designviews.layout'

    def __init__(self, parent=None):
        super(LayoutLinkEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Layout Link Editor')
        self.setMinimumSize(300, 300)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(10)
        self.setLayout(layout)

        widget = LayoutLinkEditorWidget(self)
        layout.addWidget(widget)

    def onSelectionChanged(self):
        pass
