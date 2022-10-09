"""
A widget containing a collection of panels with tools
for designing the rig blueprint.
"""

from .core import PulseWindow, PulsePanelWidget
from .designviews.controls import ControlsDesignPanel
from .designviews.general import GeneralDesignPanel
from .designviews.joints import JointsDesignPanel, DesignPanelJointOrients
from .designviews.layout import LayoutDesignPanel
from .designviews.sym import SymmetryDesignPanel
from .designviews.weights import WeightsDesignPanel
from ..vendor.Qt import QtWidgets, QtCore

PANEL_DEFINITIONS = [
    {
        "title": "General",
        "widgetClass": GeneralDesignPanel,
    },
    {
        "title": "Layout",
        "widgetClass": LayoutDesignPanel,
    },
    {
        "title": "Controls",
        "widgetClass": ControlsDesignPanel,
    },
    {
        "title": "Joints",
        "widgetClass": JointsDesignPanel,
    },
    {
        "title": "Joint Orients",
        "widgetClass": DesignPanelJointOrients,
    },
    {
        "title": "Symmetry",
        "widgetClass": SymmetryDesignPanel,
    },
    {
        "title": "Weights",
        "widgetClass": WeightsDesignPanel,
    },
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

        self.setup_panels_ui(self.scrollLayout, self.scrollWidget)

        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding)
        self.scrollLayout.addItem(spacer)

        self.scrollWidget.setLayout(self.scrollLayout)

    def setup_panels_ui(self, layout, parent):
        """
        Create a PulsePanelWidget widget for each entry in self.panelDefinitions and add it to the layout.
        """
        for panelDef in self.panelDefinitions:
            # create a collapsible container to wrap the design panel
            panel_widget = PulsePanelWidget(parent)
            panel_widget.set_title_text(panelDef['title'])

            # create the contents widget
            content_widget = panelDef['widgetClass'](parent)
            panel_widget.set_content_widget(content_widget)

            layout.addWidget(panel_widget)

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
