
import os
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui


__all__ = [
    'clearLayout',
    'getIcon',
    'getIconPath',
    'getIconPixmap',
]

ICON_DIR = os.path.join(os.path.dirname(__file__), 'icons')


def getIconPath(filename):
    """
    Return the full path to an icon by name

    Args:
        filename: A string representing the icon's file name
    """
    return os.path.join(ICON_DIR, filename)

def getIconPixmap(filename):
    """
    Return a QPixmap for an icon by name

    Args:
        filename: A string representing the icon's file name
    """
    return QtGui.QPixmap(getIconPath(filename))

def getIcon(filename):
    """
    Return a QIcon for an icon by name

    Args:
        filename: A string representing the icon's file name
    """
    return QtGui.QIcon(getIconPath(filename))

def clearLayout(layout):
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().setParent(None)
        if item.layout():
            clearLayout(item.layout())
