"""
General UI utilities for simplifying UI creation code.
"""

import logging
import os
import traceback
from functools import partial

import maya.cmds as cmds

from ..vendor.Qt import QtCore, QtWidgets, QtGui

LOG = logging.getLogger(__name__)

ICON_DIR = os.path.join(os.path.dirname(__file__), 'icons')

# mel command that will execute the last repeatable func
_REPEAT_COMMAND = 'python("{0}._repeatLastFunc()")'.format(__name__)
# reference to the last repeatable func
_REPEATABLE_FUNC = None

_DPI_SCALE = 1.0
if hasattr(cmds, "mayaDpiSetting"):
    _DPI_SCALE = cmds.mayaDpiSetting(q=True, realScaleValue=True)


def _repeatLastFunc():
    """
    Rerun the last repeatable function.
    """
    if _REPEATABLE_FUNC is not None:
        _REPEATABLE_FUNC()


def _softUpdateWrapper(wrapper, wrapped):
    """
    Update a wrapper function to look like the wrapped function.
    Like functools.update_wrapper, but doesn't fail when attributes
    are not found.
    """
    attrs = ['__name__', '__doc__']
    for attr in attrs:
        if hasattr(wrapped, attr):
            setattr(wrapper, attr, getattr(wrapped, attr))
    return wrapper


def _softWraps(wrapped):
    """
    Decorator for calling _softUpdateWrapper for a wrapped function.
    """
    return partial(_softUpdateWrapper, wrapped=wrapped)


def repeatable(func):
    """
    Decorator for making a function repeatable after it has
    been executed using Maya's repeatLast functionality.
    """

    @_softWraps(func)
    def wrapper(*args, **kwargs):
        global _REPEATABLE_FUNC
        _REPEATABLE_FUNC = partial(func, *args, **kwargs)

        result = func(*args, **kwargs)

        try:
            cmds.repeatLast(
                ac=_REPEAT_COMMAND,
                acl=func.__name__)
        except RuntimeError:
            pass

        return result

    return wrapper


def repeatPartial(func, *args, **kwargs):
    """
    Return a partial function wrapper that is repeatable.
    """
    return partial(repeatable(func), *args, **kwargs)


def undoable(func):
    """
    Decorator for making a function that will execute
    as a single undo chunk.
    """

    @_softWraps(func)
    def wrapper(*args, **kwargs):
        cmds.undoInfo(openChunk=True)
        try:
            func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            cmds.error(e)
        finally:
            cmds.undoInfo(closeChunk=True)

    return wrapper


def undoPartial(func, *args, **kwargs):
    """
    Return a partial function wrapper that is undoable.
    """
    return partial(undoable(func), *args, **kwargs)


def undoAndRepeatable(func):
    """
    Decorator that makes a function both undoable and repeatable.
    """
    return repeatable(undoable(func))


def undoAndRepeatPartial(func, *args, **kwargs):
    """
    Return a partial function wrapper that is undoable and repeatable.
    """
    return partial(undoAndRepeatable(func), *args, **kwargs)


def dpiScale(value):
    return value * _DPI_SCALE


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


def createHSpacer(width=20, height=20):
    return QtWidgets.QSpacerItem(
        20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)


def createVSpacer(width=20, height=20):
    return QtWidgets.QSpacerItem(
        20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)


def addItemsToGrid(gridLayout, items):
    """
    Add a 2-dimensional array of items to a grid layout.
    Assumes the grid layout is empty.

    Args:
        gridLayout (QGridLayout): A grid layout
        items (list): A list of rows, where each row is a list of
            QWidget, QLayoutItem, or QLayout
            E.g. [[item1, item2], [item3, item4]]
    """
    for row, itemRow in enumerate(items):
        for col, item in enumerate(itemRow):
            if item is not None:
                if isinstance(item, QtWidgets.QWidget):
                    gridLayout.addWidget(item, row, col, 1, 1)
                elif isinstance(item, QtWidgets.QLayoutItem):
                    gridLayout.addItem(item, row, col, 1, 1)
                elif isinstance(item, QtWidgets.QLayout):
                    gridLayout.addLayout(item, row, col, 1, 1)


class CollapsibleFrame(QtWidgets.QFrame):
    """
    A QFrame that can be collapsed when clicked.
    """

    collapsedChanged = QtCore.Signal(bool)

    def __init__(self, parent):
        super(CollapsibleFrame, self).__init__(parent)
        self._isCollapsed = False

    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setIsCollapsed(not self._isCollapsed)
        else:
            return super(CollapsibleFrame, self).mouseReleaseEvent(QMouseEvent)

    def setIsCollapsed(self, newCollapsed):
        """
        Set the collapsed state of this frame.
        """
        self._isCollapsed = newCollapsed
        self.collapsedChanged.emit(self._isCollapsed)

    def isCollapsed(self):
        """
        Return True if the frame is currently collapsed.
        """
        return self._isCollapsed
