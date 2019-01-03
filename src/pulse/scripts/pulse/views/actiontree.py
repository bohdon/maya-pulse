
import pulse
from pulse.vendor.Qt import QtCore, QtWidgets
from .core import PulseWindow
from .core import BlueprintUIModel

from .actionpalette import ActionPaletteWidget


__all__ = [
    'ActionTreeWidget',
    'ActionTreeWindow',
]


class ActionTreeWidget(QtWidgets.QWidget):
    """
    A tree view that displays all BuildActions in a Blueprint.
    Items can be selected, and the shared selection model
    can then be used to display info about selected BuildActions
    in other UI.
    """

    def __init__(self, parent=None):
        super(ActionTreeWidget, self).__init__(parent=parent)

        # get shared models
        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel
        self.selectionModel = self.blueprintModel.buildStepSelectionModel

        self.setupUi(self)

        # connect signals
        self.model.modelReset.connect(self.onModelReset)

    def eventFilter(self, widget, event):
        if widget is self.treeView:
            if event.type() == QtCore.QEvent.KeyPress:
                key = event.key()
                if key == QtCore.Qt.Key_Delete:
                    self.deleteSelectedItems()
                    return True
        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        self.treeView = QtWidgets.QTreeView(parent)
        self.treeView.setHeaderHidden(True)
        self.treeView.setDragEnabled(True)
        self.treeView.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.treeView.setDefaultDropAction(
            QtCore.Qt.DropAction.MoveAction)
        self.treeView.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView.setIndentation(14)
        self.treeView.installEventFilter(self)
        self.treeView.setModel(self.model)
        self.treeView.setSelectionModel(self.selectionModel)
        self.treeView.expandAll()
        layout.addWidget(self.treeView)

    def onModelReset(self):
        self.treeView.expandAll()

    def deleteSelectedItems(self):
        while True:
            indexes = self.selectionModel.selectedIndexes()
            if not indexes:
                break
            if not self.model.removeRow(indexes[0].row(), indexes[0].parent()):
                break


class ActionTreeWindow(PulseWindow):
    """
    A standalone window that contains an ActionTreeWidget
    and an ActionPaletteWidget.
    """

    OBJECT_NAME = 'pulseActionTreeWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.actiontree'

    def __init__(self, parent=None):
        super(ActionTreeWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Tree')

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.actionTree = ActionTreeWidget(self)
        layout.addWidget(self.actionTree)

        self.actionPalette = ActionPaletteWidget(self)
        layout.addWidget(self.actionPalette)

        layout.setStretch(layout.indexOf(self.actionTree), 2)
        layout.setStretch(layout.indexOf(self.actionPalette), 1)
