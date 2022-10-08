"""
A widget containing a collection of panels with tools
for designing the rig blueprint.
"""

from .core import PulseWindow
from .designviews.controls import ControlsPanel
from .designviews.general import GeneralPanel
from .designviews.joints import JointsPanel, JointOrientsPanel
from .designviews.layout import LayoutPanel
from .designviews.sym import SymmetryPanel
from .designviews.weights import WeightsPanel
from ..vendor.Qt import QtWidgets, QtCore

PANEL_DEFINITIONS = [
    {"widgetClass": GeneralPanel},
    {"widgetClass": LayoutPanel},
    {"widgetClass": ControlsPanel},
    {"widgetClass": JointsPanel},
    {"widgetClass": JointOrientsPanel},
    {"widgetClass": SymmetryPanel},
    {"widgetClass": WeightsPanel},
]


class DesignToolkitWidget(QtWidgets.QWidget):
    """
    A widget containing a collection of panels with tools
    for designing the rig blueprint.
    """

    def __init__(self, parent=None):
        super(DesignToolkitWidget, self).__init__(parent=parent)

        # list of panel widgets to add, in order
        self.panelDefinitions = PANEL_DEFINITIONS

        self.setupUi(self)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        self.scrollArea = QtWidgets.QScrollArea(parent)
        self.scrollArea.setFrameShape(QtWidgets.QScrollArea.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        layout.addWidget(self.scrollArea)

        self.scrollWidget = QtWidgets.QWidget()
        self.scrollArea.setWidget(self.scrollWidget)

        # scroll layout contains the main layout and a spacer item
        self.scrollLayout = QtWidgets.QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setMargin(0)
        self.scrollLayout.setSpacing(8)

        self.setupPanelsUi(self.scrollLayout, self.scrollWidget)

        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding)
        self.scrollLayout.addItem(spacer)

        self.scrollWidget.setLayout(self.scrollLayout)

    def setupPanelsUi(self, layout, parent):
        """
        Create a widget instance for each class in self.panelDefinitions
        and add it to the layout.
        """
        for panelDef in self.panelDefinitions:
            panel = panelDef['widgetClass'](parent)
            layout.addWidget(panel)

        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)


class DesignToolkitWindow(PulseWindow):
    OBJECT_NAME = 'pulseDesignToolkitWindow'
    PREFERRED_SIZE = QtCore.QSize(280, 300)
    STARTING_SIZE = QtCore.QSize(280, 300)
    MINIMUM_SIZE = QtCore.QSize(280, 300)
    DEFAULT_TAB_CONTROL = 'ChannelBoxLayerEditor'
    WINDOW_MODULE = 'pulse.ui.designview'

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle('Pulse Design Toolkit')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.setLayout(layout)

        widget = DesignToolkitWidget(self)
        layout.addWidget(widget)
