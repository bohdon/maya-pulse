import pymel.core as pm
from maya import OpenMaya as api

from .. import utils as viewutils
from ..core import PulseWindow, PulsePanelWidget
from ..gen.layout_link_editor import Ui_LayoutLinkEditor
from ..utils import undoAndRepeatPartial as cmd
from ... import editorutils
from ... import links
from ...vendor.Qt import QtCore, QtWidgets, QtGui


class LayoutPanel(PulsePanelWidget):
    """
    The layout utils panel shown in the Design Toolkit.
    """

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
    """
    The link editor widget shown when launching Link Editor from the design panel.
    """

    def __init__(self, parent):
        super(LayoutLinkEditorWidget, self).__init__(parent=parent)

        self.selection_changed_cb = None
        self.link_info_list = None

        self.ui = Ui_LayoutLinkEditor()
        self.ui.setupUi(self)

        self.ui.link_btn.clicked.connect(cmd(self.link_selected, linkType=links.LinkType.DEFAULT))
        self.ui.link_ikpole_btn.clicked.connect(cmd(self.link_selected, linkType=links.LinkType.IKPOLE))
        self.ui.link_center_btn.clicked.connect(cmd(self.link_selected_weighted))
        self.ui.recreate_link_btn.clicked.connect(cmd(self.recreate_links_for_selected))
        self.ui.unlink_btn.clicked.connect(cmd(self.unlink_selected))
        self.ui.snap_to_targets_btn.clicked.connect(cmd(editorutils.positionLinkForSelected))
        self.ui.refresh_btn.clicked.connect(self.update_link_info_list)

    def showEvent(self, event):
        super(LayoutLinkEditorWidget, self).showEvent(event)
        if self.selection_changed_cb is None:
            print('adding selection changed callback')
            self.selection_changed_cb = api.MEventMessage.addEventCallback("SelectionChanged",
                                                                           self.onSceneSelectionChanged)
        self.update_link_info_list()

    def hideEvent(self, event):
        super(LayoutLinkEditorWidget, self).hideEvent(event)
        if self.selection_changed_cb is not None:
            print('removing selection changed callback')
            api.MMessage.removeCallback(self.selection_changed_cb)
            self.selection_changed_cb = None

    def onSceneSelectionChanged(self, *args, **kwargs):
        self.update_link_info_list()

    @property
    def keep_offsets(self):
        return self.ui.keep_offsets_check.isChecked()

    def update_link_info_list(self):
        if self.link_info_list:
            self.link_info_list.deleteLater()
            self.link_info_list = None

        # get selected nodes and link data
        sel_nodes = pm.selected()
        self.link_info_list = LinkInfoListWidget(self, sel_nodes)
        self.ui.link_info_scroll_area.setWidget(self.link_info_list)

    def link_selected(self, linkType):
        editorutils.linkSelected(linkType, self.keep_offsets)
        self.update_link_info_list()

    def link_selected_weighted(self):
        editorutils.linkSelectedWeighted(self.keep_offsets)
        self.update_link_info_list()

    def recreate_links_for_selected(self):
        editorutils.recreateLinksForSelected(self.keep_offsets)
        self.update_link_info_list()

    def unlink_selected(self):
        editorutils.unlinkSelected()
        self.update_link_info_list()


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

        if not isinstance(linkData, dict):
            linkData = {}

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

        # get link data keys, sorted with `type` and `targetNodes` first
        keys = ['type', 'targetNodes']
        keys += [k for k in self.linkData.keys() if k not in keys]

        # create labels for each piece of data
        for key in keys:
            value = self.linkData.get(key)
            nameLabel = QtWidgets.QLabel(parent)
            nameLabel.setText(key)
            valueLabel = QtWidgets.QLabel(parent)
            valueLabel.setText(str(value))

            # add new items to list of pending grid items
            gridItems.append([nameLabel, valueLabel])

        viewutils.addItemsToGrid(gridLayout, gridItems)

        self.setLayout(layout)


class LayoutLinkEditorWindow(PulseWindow):
    """
    Window containing the LayoutLinkEditorWidget.
    """

    OBJECT_NAME = 'pulseLayoutLinkEditorWindow'
    WINDOW_MODULE = 'pulse.ui.designviews.layout'

    def __init__(self, parent=None):
        super(LayoutLinkEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Layout Link Editor')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(10)
        self.setLayout(layout)

        widget = LayoutLinkEditorWidget(self)
        layout.addWidget(widget)

    def onSelectionChanged(self):
        pass
