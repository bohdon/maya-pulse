"""
A widget containing a collection of panels with tools
for working with skinned meshes.
"""

from .skinviews.manage import ManageWeightsPanel
from ..vendor.Qt import QtWidgets

PANEL_DEFINITIONS = [
    {"widgetClass": ManageWeightsPanel},
]


class SkinViewWidget(QtWidgets.QWidget):
    """
    A widget containing a collection of panels with tools
    for working with skinned meshes.
    """

    def __init__(self, parent=None):
        super(SkinViewWidget, self).__init__(parent=parent)

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
