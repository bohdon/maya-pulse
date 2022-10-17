"""
Widget for quickly editing the color of animation controls.
"""

from ..colors import LinearColor
from ..vendor.Qt import QtCore, QtWidgets
from .core import PulseWindow, BlueprintUIModel
from .utils import undoAndRepeatPartial as cmd
from .. import editorutils


class QuickColorWidget(QtWidgets.QWidget):
    """
    Widget for quickly editing the color of animation controls.
    """

    def __init__(self, parent=None):
        super(QuickColorWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        # the blueprint config
        self.config = self._getConfig()

        self.setupUi(self)

        if True:  # TODO: replace with 'is blueprint initialized' or similar
            self.helpText.setText("Edit the Blueprint Config to modify colors")
            self.helpText.setProperty('cssClasses', 'help')
        elif self.config:
            self.helpText.setText("No Blueprint exists, using the default config")
            self.helpText.setProperty('cssClasses', 'help warning')
        else:
            self.helpText.setText("No Blueprint config was found")
            self.helpText.setProperty('cssClasses', 'help errror')
        # refresh style for css classes
        self.helpText.setStyleSheet('')

    def _getConfig(self):
        config = self.blueprintModel.blueprint.get_config()
        return config if config else {}

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        # clear color btn
        clearBtn = QtWidgets.QPushButton(parent)
        clearBtn.setText("Remove Color")
        clearBtn.clicked.connect(cmd(editorutils.disableColorOverrideForSelected))
        layout.addWidget(clearBtn)

        bodyLayout = self.setupBodyUi(parent)
        layout.addLayout(bodyLayout)

        # help text
        self.helpText = QtWidgets.QLabel()
        self.helpText.setProperty('cssClasses', 'help')
        layout.addWidget(self.helpText)

        layout.setStretch(2, 1)

    def setupBodyUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        config_colors = self.config.get('colors', {})
        for name, hex_color in config_colors.items():
            color = LinearColor.from_hex(hex_color)
            btn = self.createColorButton(name, color, parent)
            layout.addWidget(btn)

        return layout

    def createColorButton(self, name: str, color: LinearColor, parent):
        btn = QtWidgets.QPushButton(parent)
        btn.setText(name)
        btn.setStyleSheet(color.as_bg_style())
        btn.clicked.connect(cmd(editorutils.setOverrideColorForSelected, color))
        return btn


class QuickColorWindow(PulseWindow):
    OBJECT_NAME = 'pulseQuickColorWindow'
    PREFERRED_SIZE = QtCore.QSize(200, 300)
    STARTING_SIZE = QtCore.QSize(200, 300)
    MINIMUM_SIZE = QtCore.QSize(200, 300)

    WINDOW_MODULE = 'pulse.ui.quickcolor'

    def __init__(self, parent=None):
        super(QuickColorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Quick Color Editor')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.setLayout(layout)

        widget = QuickColorWidget(self)
        layout.addWidget(widget)
