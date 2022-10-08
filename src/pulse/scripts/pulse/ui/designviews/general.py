import pymel.core as pm

from .. import utils as viewutils
from ..core import PulsePanelWidget
from ..quickcolor import QuickColorWindow
from ..quickname import QuickNameWindow
from ..utils import undoAndRepeatPartial as cmd
from ... import editorutils
from ...vendor.Qt import QtWidgets


class GeneralPanel(PulsePanelWidget):

    def __init__(self, parent):
        super(GeneralPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "General"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        gridLayout = QtWidgets.QGridLayout(frame)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        nameEditorBtn = QtWidgets.QPushButton(frame)
        nameEditorBtn.setText("Name Editor")
        nameEditorBtn.clicked.connect(
            cmd(QuickNameWindow.toggleWindow))

        colorEditorBtn = QtWidgets.QPushButton(frame)
        colorEditorBtn.setText("Color Editor")
        colorEditorBtn.clicked.connect(
            cmd(QuickColorWindow.toggleWindow))

        parentSelBtn = QtWidgets.QPushButton(frame)
        parentSelBtn.setText("Parent Selected")
        parentSelBtn.setStatusTip(
            "Parent the selected nodes, select one leader then followers")
        parentSelBtn.clicked.connect(cmd(editorutils.parentSelected))

        parentInOrderBtn = QtWidgets.QPushButton(frame)
        parentInOrderBtn.setText("Parent in Order")
        parentInOrderBtn.setStatusTip(
            "Parent the selection in order, select leaders to followers")
        parentInOrderBtn.clicked.connect(
            cmd(editorutils.parentSelectedInOrder))

        createOffsetBtn = QtWidgets.QPushButton(frame)
        createOffsetBtn.setText("Create Offset")
        createOffsetBtn.setStatusTip(
            "Group the selected transform, creating the group "
            "exactly where the transform is")
        createOffsetBtn.clicked.connect(
            cmd(editorutils.createOffsetForSelected))

        selectChildrenBtn = QtWidgets.QPushButton(frame)
        selectChildrenBtn.setText("Select Hierarchy")
        selectChildrenBtn.setStatusTip(
            "Select all descendants of the selected node")
        selectChildrenBtn.clicked.connect(cmd(self.selectChildren))

        freezeScaleBtn = QtWidgets.QPushButton(frame)
        freezeScaleBtn.setText("Freeze Scales")
        freezeScaleBtn.setStatusTip(
            "Freeze the scales of the selected node and its children "
            "without affecting their pivots")
        freezeScaleBtn.clicked.connect(
            cmd(editorutils.freezeScalesForSelectedHierarchies))

        freezePivotBtn = QtWidgets.QPushButton(frame)
        freezePivotBtn.setText("Freeze Pivots")
        freezePivotBtn.setStatusTip(
            "Freeze the local pivots of the selected node and its "
            "children by baking the values into translate")
        freezePivotBtn.clicked.connect(
            cmd(editorutils.freezePivotsForSelectedHierarchies))

        gridItems = [
            [nameEditorBtn, colorEditorBtn],
            [parentSelBtn, parentInOrderBtn],
            [createOffsetBtn, selectChildrenBtn],
            [freezeScaleBtn, freezePivotBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)

    def selectChildren(self):
        """
        Select all child nodes. Similar to select hierarchy except
        only transforms or joints are selected.
        """
        objs = []
        for obj in pm.selected():
            objs.extend(obj.listRelatives(
                ad=True, type=['transform', 'joint']))
        pm.select(objs, add=True)
