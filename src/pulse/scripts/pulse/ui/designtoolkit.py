"""
A toolkit for setting up pulse blueprints including control and joint creation,
joint orienting, symmetry and other design tools.
"""

from .core import PulseWindow, PulsePanelWidget
from .designviews.controls import ControlsDesignPanel
from .designviews.general import GeneralDesignPanel
from .designviews.joints import JointsDesignPanel, DesignPanelJointOrients
from .designviews.layout import LayoutDesignPanel
from .designviews.sym import SymmetryDesignPanel
from .designviews.weights import WeightsDesignPanel
from .gen.design_toolkit import Ui_DesignToolkit
from ..vendor.Qt import QtWidgets

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


class DesignToolkit(QtWidgets.QWidget):
    """
    A widget containing a collection of panels with tools
    for designing the rig blueprint.
    """

    def __init__(self, parent=None):
        super(DesignToolkit, self).__init__(parent=parent)

        # list of panel widgets to add, in order
        self.panelDefinitions = PANEL_DEFINITIONS

        self.ui = Ui_DesignToolkit()
        self.ui.setupUi(self)

        self.setup_panels_ui(self.ui.main_layout, self.ui.scroll_area_widget)

    def setup_panels_ui(self, layout, parent):
        """
        Create a PulsePanelWidget widget for each entry in self.panelDefinitions and add it to the layout.
        """
        for panelDef in self.panelDefinitions:
            # create a collapsible container to wrap the design panel
            panel_widget = PulsePanelWidget(parent)
            panel_widget.set_title_text(panelDef["title"])

            # create the contents widget
            content_widget = panelDef["widgetClass"](parent)
            panel_widget.set_content_widget(content_widget)

            layout.addWidget(panel_widget)


class DesignToolkitWindow(PulseWindow):
    OBJECT_NAME = "pulseDesignToolkitWindow"
    WINDOW_MODULE = "pulse.ui.designtoolkit"

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Pulse Design Toolkit")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        widget = DesignToolkit(self)
        layout.addWidget(widget)
