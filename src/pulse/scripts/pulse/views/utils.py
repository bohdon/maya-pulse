
import os
from Qt import QtCore, QtWidgets, QtGui


__all__ = [
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
