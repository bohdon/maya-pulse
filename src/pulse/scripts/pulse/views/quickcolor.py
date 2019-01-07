
import pymel.core as pm
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse.core
import pulse.colors
import pulse.editorutils
from .core import PulseWindow, BlueprintUIModel
from .utils import undoAndRepeatPartial as cmd
from . import style

__all__ = [
    "QuickColorWidget",
    "QuickColorWindow",
]


class QuickColorWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(QuickColorWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        # the blueprint config
        self.config = self._getConfig()

        self.setupUi(self)

        if True:  # TODO: replace with 'is blueprint initialized' or similar
            self.helpText.setText(
                "Edit the Blueprint Config to modify naming keywords")
            self.helpText.setStyleSheet(
                style.UIColors.asFGColor(style.UIColors.HELPTEXT))
        elif self.config:
            self.helpText.setText(
                "No Blueprint exists, using the default config")
            self.helpText.setStyleSheet(
                style.UIColors.asFGColor(style.UIColors.WARNING))
        else:
            self.helpText.setText(
                "No Blueprint config was found")
            self.helpText.setStyleSheet(
                style.UIColors.asFGColor(style.UIColors.ERROR))

    def _getConfig(self):
        # if self.blueprintModel.blueprintExists():
        if True:
            config = self.blueprintModel.blueprint.getConfig()
        else:
            config = pulse.core.blueprints.loadDefaultConfig()
        return config if config else {}

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        # clear color btn
        clearBtn = QtWidgets.QPushButton(parent)
        clearBtn.setText("Remove Color")
        clearBtn.clicked.connect(
            cmd(pulse.editorutils.disableColorOverrideForSelected))
        layout.addWidget(clearBtn)

        bodyLayout = self.setupBodyUi(parent)
        layout.addLayout(bodyLayout)

        # help text
        self.helpText = QtWidgets.QLabel()
        self.helpText.setFont(style.UIFonts.getHelpTextFont())
        layout.addWidget(self.helpText)

        layout.setStretch(2, 1)

    def setupBodyUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        colors = self.config.get('colors', [])
        for colorData in colors:
            if 'name' in colorData and 'color' in colorData:
                name = colorData['name']
                color = pulse.colors.hexToRGB01(colorData['color'])
                btn = self.createColorButton(name, color, parent)
                layout.addWidget(btn)

        return layout

    def createColorButton(self, name, color, parent):
        btn = QtWidgets.QPushButton(parent)
        btn.setText(name)
        # colors are given in range 0..1, convert to 0..255 for Qt
        btn.setStyleSheet(style.UIColors.asBGColor([c * 255 for c in color]))
        btn.clicked.connect(
            cmd(pulse.editorutils.setOverrideColorForSelected, color))
        return btn


class QuickColorWindow(PulseWindow):

    OBJECT_NAME = 'pulseQuickColorWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.quickcolor'

    def __init__(self, parent=None):
        super(QuickColorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Quick Color Editor')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.setLayout(layout)

        widget = QuickColorWidget(self)
        layout.addWidget(widget)
