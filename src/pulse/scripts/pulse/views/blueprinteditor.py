
import pulse
from pulse.vendor.Qt import QtWidgets
from .core import PulseWindow
from .core import BlueprintUIModel
from .style import UIColors


__all__ = [
    'BlueprintEditorWidget',
    'BlueprintEditorWindow',
]


class BlueprintEditorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(BlueprintEditorWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel

        self.setupUi(self)

        self.blueprintModel.blueprintCreated.connect(self.refreshState)
        self.blueprintModel.blueprintDeleted.connect(self.refreshState)
        self.blueprintModel.rigNameChanged.connect(self.onRigNameChanged)

    def showEvent(self, event):
        super(BlueprintEditorWidget, self).showEvent(event)
        self.blueprintModel.addSubscriber(self)

    def hideEvent(self, event):
        super(BlueprintEditorWidget, self).hideEvent(event)
        self.blueprintModel.removeSubscriber(self)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(self)

        self.rigNameText = QtWidgets.QLineEdit(self)
        self.rigNameText.setText(self.blueprintModel.getRigName())
        self.rigNameText.textChanged.connect(self.rigNameTextChanged)
        layout.addWidget(self.rigNameText)

        debugPrintBtn = QtWidgets.QPushButton(self)
        debugPrintBtn.setText("Debug Print Serialized")
        debugPrintBtn.clicked.connect(self.debugPrintSerialized)
        layout.addWidget(debugPrintBtn)

        self.deleteBtn = QtWidgets.QPushButton(self)
        self.deleteBtn.setText("Delete Blueprint")
        self.deleteBtn.clicked.connect(self.blueprintModel.deleteNode)
        layout.addWidget(self.deleteBtn)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

        self.refreshState()

    def refreshState(self):
        self.rigNameText.setEnabled(not self.blueprintModel.isReadOnly())
        self.deleteBtn.setEnabled(not self.blueprintModel.isReadOnly())
        if self.deleteBtn.isEnabled():
            self.deleteBtn.setStyleSheet(UIColors.asBGColor(UIColors.RED))
        else:
            self.deleteBtn.setStyleSheet('')

    def onRigNameChanged(self, name):
        self.rigNameText.setText(name)

    def rigNameTextChanged(self):
        self.blueprintModel.setRigName(self.rigNameText.text())

    def debugPrintSerialized(self):
        import pprint
        if self.blueprintModel.blueprint:
            pprint.pprint(self.blueprintModel.blueprint.serialize())
        else:
            print('No Blueprint')



class BlueprintEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseBlueprintEditorWindow'

    def __init__(self, parent=None):
        super(BlueprintEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Blueprint Editor')

        widget = BlueprintEditorWidget(self)
        self.setCentralWidget(widget)
