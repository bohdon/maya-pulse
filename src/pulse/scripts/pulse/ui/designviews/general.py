import pymel.core as pm

from ...vendor.Qt import QtWidgets
from ... import editorutils
from ..utils import undoAndRepeatPartial as cmd

from ..gen.designpanel_general import Ui_GeneralDesignPanel

from ..quickcolor import QuickColorWindow
from ..quickname import QuickNameWindow


class GeneralDesignPanel(QtWidgets.QWidget):

    def __init__(self, parent):
        super(GeneralDesignPanel, self).__init__(parent)

        self.ui = Ui_GeneralDesignPanel()
        self.ui.setupUi(self)

        self.ui.name_editor_btn.clicked.connect(cmd(QuickNameWindow.toggleWindow))
        self.ui.color_editor_btn.clicked.connect(cmd(QuickColorWindow.toggleWindow))
        self.ui.parent_selected_btn.clicked.connect(cmd(editorutils.parentSelected))
        self.ui.parent_in_order_btn.clicked.connect(cmd(editorutils.parentSelectedInOrder))
        self.ui.create_offset_btn.clicked.connect(cmd(editorutils.createOffsetForSelected))
        self.ui.select_hierarchy_btn.clicked.connect(cmd(self.select_children))
        self.ui.freeze_scales_btn.clicked.connect(cmd(editorutils.freezeScalesForSelectedHierarchies))
        self.ui.freeze_pivots_btn.clicked.connect(cmd(editorutils.freezePivotsForSelectedHierarchies))

    def select_children(self):
        """
        Select all child nodes. Similar to select hierarchy except
        only transforms or joints are selected.
        """
        objs = []
        for obj in pm.selected():
            objs.extend(obj.listRelatives(ad=True, type=['transform', 'joint']))
        pm.select(objs, add=True)
