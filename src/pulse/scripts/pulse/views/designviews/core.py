
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

__all__ = [
    "DesignViewPanel",
]


class DesignViewPanel(QtWidgets.QWidget):
    """
    Base widget for any panel in the design view.

    Provides functionality for building a consistent
    ui across all design view panels.
    """

    def getPanelDisplayName(self):
        """
        Return the display name for this panel
        """
        raise NotImplementedError

    def getPanelColor(self):
        return [0, 0, 0]

    def setupPanelUi(self, parent):
        """
        Build a collapsible panel ui that can be used
        by all design panels.

        Sets `self.panelLayout` and `self.panelFrame` which can
        be used as the layout and parent widget for the panel's
        unique contents.
        """
        self.mainLayout = QtWidgets.QVBoxLayout(parent)
        self.mainLayout.setMargin(0)
        self.mainLayout.setSpacing(2)

        # header frame
        self.headerFrame = QtWidgets.QFrame(parent)
        headerColor = 'rgba({0}, {1}, {2}, 40)'.format(*self.getPanelColor())
        self.headerFrame.setStyleSheet(".QFrame{{ background-color: {color}; border-radius: 2px; }}".format(color=headerColor))
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

        # body layout
        self.panelFrame = QtWidgets.QFrame(parent)
        self.panelFrame.setObjectName("panelFrame")
        self.panelFrame.setStyleSheet(".QFrame#panelFrame{ background-color: rgba(255, 255, 255, 5); }")
        self.panelLayout = QtWidgets.QVBoxLayout(self.panelFrame)
        self.panelLayout.setMargin(4)
        self.mainLayout.addWidget(self.panelFrame)

        return self.panelLayout, self.panelFrame
