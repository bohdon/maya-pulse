
from Qt import QtCore, QtWidgets, QtGui
import pymetanode as meta

import pulse
from pulse.views.core import PulseWindow
from pulse.views.actiontree import ActionTreeItemModel


__all__ = [
    'BlueprintEditorWidget',
    'BlueprintEditorWindow',
]


class BlueprintEditorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(BlueprintEditorWidget, self).__init__(parent=parent)

        layout = QtWidgets.QVBoxLayout(self)

        createBtn = QtWidgets.QPushButton(self)
        createBtn.setText("Create Default Blueprint")
        createBtn.clicked.connect(self.createDefaultBlueprint)
        layout.addWidget(createBtn)

        debugPrintBtn = QtWidgets.QPushButton(self)
        debugPrintBtn.setText("Debug Print Serialized")
        debugPrintBtn.clicked.connect(self.debugPrintSerialized)
        layout.addWidget(debugPrintBtn)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

    def createDefaultBlueprint(self):
        blueprint = pulse.Blueprint()
        blueprint.initializeDefaultActions()
        blueprint.saveToDefaultNode()
        ActionTreeItemModel.getSharedModel().reloadBlueprint()

    def debugPrintSerialized(self):
        import pprint
        blueprint = pulse.Blueprint.fromDefaultNode()
        if blueprint:
            pprint.pprint(blueprint.serialize())



class BlueprintEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseBlueprintEditorWindow'

    def __init__(self, parent=None):
        super(BlueprintEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        widget = BlueprintEditorWidget(self)
        self.setCentralWidget(widget)
