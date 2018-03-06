
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from maya import cmds

from pulse.views.core import CollapsibleFrame

__all__ = [
    "DesignViewPanel",
]


class DesignViewPanel(QtWidgets.QWidget):
    """
    Base widget for any panel in the design view.

    Provides functionality for building a consistent
    ui across all design view panels.
    """

    def __init__(self, parent):
        super(DesignViewPanel, self).__init__(parent=parent)

        self.setupUi(self)
        self.setupPanelUi(self.panelWidget)

    def getPanelDisplayName(self):
        """
        Return the display name for this panel
        """
        raise NotImplementedError

    def getPanelColor(self):
        return [0, 0, 0]

    def setupUi(self, parent):
        """
        Build a collapsible panel ui that can be used
        by all design panels.

        All panel widgets should be attached to `self.panelWidget`
        """
        self.mainLayout = QtWidgets.QVBoxLayout(parent)
        self.mainLayout.setMargin(0)
        self.mainLayout.setSpacing(2)

        # header frame
        self.headerFrame = CollapsibleFrame(parent)
        headerColor = 'rgba({0}, {1}, {2}, 40)'.format(*self.getPanelColor())
        self.headerFrame.setStyleSheet(".CollapsibleFrame{{ background-color: {color}; border-radius: 2px; }}".format(color=headerColor))
        self.headerFrame.collapsedChanged.connect(self.onCollapsedChanged)
        # header layout
        self.headerLayout = QtWidgets.QHBoxLayout(self.headerFrame)
        self.headerLayout.setContentsMargins(10, 2, 2, 2)
        # display name label
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.displayNameLabel = QtWidgets.QLabel(self.headerFrame)
        self.displayNameLabel.setMinimumHeight(18)
        self.displayNameLabel.setFont(font)
        self.displayNameLabel.setText(self.getPanelDisplayName())
        self.headerLayout.addWidget(self.displayNameLabel)

        self.mainLayout.addWidget(self.headerFrame)

        self.panelWidget = QtWidgets.QWidget(parent)
        self.mainLayout.addWidget(self.panelWidget)
    
    def setupPanelUi(self, parent):
        """
        Setup the ui for the contents of the panel
        """
        raise NotImplementedError
    
    def onCollapsedChanged(self, isCollapsed):
        self.panelWidget.setVisible(not isCollapsed)
    
    @staticmethod
    def createPanelFrame(parent):
        """
        Create a QFrame with consistent styling for a design view panel
        """
        frame = QtWidgets.QFrame(parent)
        frame.setObjectName("panelFrame")
        frame.setStyleSheet(".QFrame#panelFrame{ background-color: rgba(255, 255, 255, 5); }")
        return frame
