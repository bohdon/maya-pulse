import pymel.core as pm
from PySide2 import QtWidgets
from maya import OpenMaya as api

from .. import utils
from ..core import PulseWindow
from ..gen.designpanel_layout import Ui_LayoutDesignPanel
from ..gen.layout_link_editor import Ui_LayoutLinkEditor
from ..gen.layout_link_info_widget import Ui_LayoutLinkInfoWidget
from ..utils import undo_and_repeat_partial as cmd
from ... import editor_utils
from ... import links


class LayoutDesignPanel(QtWidgets.QWidget):
    """
    The layout utils panel shown in the Design Toolkit.
    """

    def __init__(self, parent):
        super(LayoutDesignPanel, self).__init__(parent)

        self.ui = Ui_LayoutDesignPanel()
        self.ui.setupUi(self)

        self.ui.snap_to_targets_btn.clicked.connect(cmd(editor_utils.position_link_for_selected))
        self.ui.link_editor_btn.clicked.connect(cmd(LayoutLinkEditorWindow.toggleWindow))


class LayoutLinkEditorWidget(QtWidgets.QWidget):
    """
    The link editor widget shown when launching Link Editor from the design panel.
    """

    def __init__(self, parent):
        super(LayoutLinkEditorWidget, self).__init__(parent=parent)

        self.selection_changed_cb = None

        self.ui = Ui_LayoutLinkEditor()
        self.ui.setupUi(self)

        self.ui.link_btn.clicked.connect(cmd(self.link_selected, link_type=links.LinkType.DEFAULT))
        self.ui.link_ikpole_btn.clicked.connect(cmd(self.link_selected, link_type=links.LinkType.IK_POLE))
        self.ui.link_center_btn.clicked.connect(cmd(self.link_selected_weighted))
        self.ui.recreate_link_btn.clicked.connect(cmd(self.recreate_links_for_selected))
        self.ui.unlink_btn.clicked.connect(cmd(self.unlink_selected))
        self.ui.snap_to_targets_btn.clicked.connect(cmd(editor_utils.position_link_for_selected))
        self.ui.refresh_btn.clicked.connect(self.update_link_info)

    def showEvent(self, event):
        super(LayoutLinkEditorWidget, self).showEvent(event)
        if self.selection_changed_cb is None:
            print("adding selection changed callback")
            self.selection_changed_cb = api.MEventMessage.addEventCallback(
                "SelectionChanged", self._on_scene_selection_changed
            )
        self.update_link_info()

    def hideEvent(self, event):
        super(LayoutLinkEditorWidget, self).hideEvent(event)
        if self.selection_changed_cb is not None:
            print("removing selection changed callback")
            api.MMessage.removeCallback(self.selection_changed_cb)
            self.selection_changed_cb = None

    def _on_scene_selection_changed(self, *args, **kwargs):
        self.update_link_info()

    @property
    def keep_offsets(self):
        return self.ui.keep_offsets_check.isChecked()

    def update_link_info(self):
        parent = self.ui.link_info_scroll_area_widget

        # get selected nodes and link data
        sel_nodes = pm.selected()
        utils.clear_layout(self.ui.link_info_vbox)

        for node in sel_nodes:
            if not links.is_linked(node):
                continue
            link_data = links.get_link_meta_data(node)
            link_info = LinkInfoWidget(parent, node, link_data)
            self.ui.link_info_vbox.addWidget(link_info)

    def link_selected(self, link_type):
        editor_utils.link_selected(link_type, self.keep_offsets)
        self.update_link_info()

    def link_selected_weighted(self):
        editor_utils.link_selected_weighted(self.keep_offsets)
        self.update_link_info()

    def recreate_links_for_selected(self):
        editor_utils.recreate_links_for_selected(self.keep_offsets)
        self.update_link_info()

    def unlink_selected(self):
        editor_utils.unlink_selected()
        self.update_link_info()


class LinkInfoWidget(QtWidgets.QWidget):
    """
    Displays info about a linked node
    """

    def __init__(self, parent, node, link_data):
        super(LinkInfoWidget, self).__init__(parent=parent)
        if not node:
            raise ValueError("Node must be a valid PyNode")

        if not isinstance(link_data, dict):
            link_data = {}

        self.node = node
        self.linkData = link_data

        self.ui = Ui_LayoutLinkInfoWidget()
        self.ui.setupUi(self)

        self.setup_metadata_ui(self)

        self.ui.name_label.setText(self.node.name())

    def setup_metadata_ui(self, parent):
        # get link data keys, sorted with `type` and `targetNodes` first
        keys = ["type", "targetNodes"]
        keys += [k for k in self.linkData.keys() if k not in keys]

        # create labels for each piece of data
        row = 0
        for key in keys:
            name_label = QtWidgets.QLabel(parent)
            name_label.setText(key)

            value_label = QtWidgets.QLabel(parent)
            value_label.setText(str(self.linkData.get(key)))

            # add new items to list of pending grid items
            self.ui.metadata_form.setWidget(row, QtWidgets.QFormLayout.LabelRole, name_label)
            self.ui.metadata_form.setWidget(row, QtWidgets.QFormLayout.FieldRole, value_label)
            row += 1


class LayoutLinkEditorWindow(PulseWindow):
    """
    Window containing the LayoutLinkEditorWidget.
    """

    OBJECT_NAME = "pulseLayoutLinkEditorWindow"
    WINDOW_MODULE = "pulse.ui.designviews.layout"

    def __init__(self, parent=None):
        super(LayoutLinkEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle("Layout Link Editor")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.setLayout(layout)

        widget = LayoutLinkEditorWidget(self)
        layout.addWidget(widget)
