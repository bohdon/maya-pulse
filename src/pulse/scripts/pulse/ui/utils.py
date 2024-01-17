"""
General UI utilities for simplifying UI creation code.
"""

import logging
import os
import traceback
from functools import partial
from typing import Optional, Callable

import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets, QtGui
from maya.OpenMayaUI import MQtUtil
from shiboken2 import wrapInstance

LOG = logging.getLogger(__name__)

ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")

# mel command that will execute the last repeatable func
_REPEAT_COMMAND = 'python("{0}._repeat_last_func()")'.format(__name__)
# reference to the last repeatable func
_REPEATABLE_FUNC = None

_DPI_SCALE = 1.0
if hasattr(cmds, "mayaDpiSetting"):
    _DPI_SCALE = cmds.mayaDpiSetting(q=True, realScaleValue=True)


def _repeat_last_func():
    """
    Rerun the last repeatable function.
    """
    if _REPEATABLE_FUNC is not None:
        _REPEATABLE_FUNC()


def _soft_update_wrapper(wrapper, wrapped):
    """
    Update a wrapper function to look like the wrapped function.
    Like functools.update_wrapper, but doesn't fail when attributes
    are not found.
    """
    attrs = ["__name__", "__doc__"]
    for attr in attrs:
        if hasattr(wrapped, attr):
            setattr(wrapper, attr, getattr(wrapped, attr))
    return wrapper


def _soft_wraps(wrapped):
    """
    Decorator for calling _soft_update_wrapper for a wrapped function.
    """
    return partial(_soft_update_wrapper, wrapped=wrapped)


def repeatable(func):
    """
    Decorator for making a function repeatable after it has
    been executed using Maya's repeatLast functionality.
    """

    @_soft_wraps(func)
    def wrapper(*args, **kwargs):
        global _REPEATABLE_FUNC
        _REPEATABLE_FUNC = partial(func, *args, **kwargs)

        result = func(*args, **kwargs)

        try:
            cmds.repeatLast(ac=_REPEAT_COMMAND, acl=func.__name__)
        except RuntimeError:
            pass

        return result

    return wrapper


def repeat_partial(func, *args, **kwargs):
    """
    Return a partial function wrapper that is repeatable.
    """
    return partial(repeatable(func), *args, **kwargs)


def undoable(func):
    """
    Decorator for making a function that will execute
    as a single undo chunk.
    """

    @_soft_wraps(func)
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


def undo_partial(func, *args, **kwargs):
    """
    Return a partial function wrapper that is undoable.
    """
    return partial(undoable(func), *args, **kwargs)


def undo_and_repeatable(func):
    """
    Decorator that makes a function both undoable and repeatable.
    """
    return repeatable(undoable(func))


def undo_and_repeat_partial(func, *args, **kwargs):
    """
    Return a partial function wrapper that is undoable and repeatable.
    """
    return partial(undo_and_repeatable(func), *args, **kwargs)


def dpi_scale(value):
    return value * _DPI_SCALE


def get_icon_path(filename):
    """
    Return the full path to an icon by name

    Args:
        filename: A string representing the icon's file name
    """
    return os.path.join(ICON_DIR, filename)


def get_icon_pixmap(filename):
    """
    Return a QPixmap for an icon by name

    Args:
        filename: A string representing the icon's file name
    """
    return QtGui.QPixmap(get_icon_path(filename))


def get_icon(filename):
    """
    Return a QIcon for an icon by name

    Args:
        filename: A string representing the icon's file name
    """
    return QtGui.QIcon(get_icon_path(filename))


def get_maya_pixmap(name: str) -> Optional[QtGui.QPixmap]:
    """
    Return a pixmap from Maya's internal resources using MQtUtil.
    """
    ptr = MQtUtil.createPixmap(name)
    if ptr:
        return wrapInstance(int(ptr), QtGui.QPixmap)


def get_rmb_menu_cursor() -> QtGui.QCursor:
    """
    Return the mouse cursor to use for rmb menus.
    """
    ptr = MQtUtil.createCursor("rmbMenu.png,11,9,17,14,22,18")
    return wrapInstance(int(ptr), QtGui.QCursor)


def set_custom_context_menu(widget: QtWidgets.QWidget, callback: Callable):
    """
    Configure a widget to have a custom context menu, built with a custom callback.
    Also configures the widget with the right click menu cursor icon and ensures
    the menu appears on right click press instead of release to be consistent with Maya behavior.
    """
    widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    widget.customContextMenuRequested.connect(callback)
    widget.setCursor(get_rmb_menu_cursor())
    event_filter = RightClickMenuOnPressEventFilter(widget)
    widget.installEventFilter(event_filter)


def clear_layout(layout):
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().setParent(None)
        if item.layout():
            clear_layout(item.layout())


def create_h_spacer(width=20, height=20):
    return QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)


def create_v_spacer(width=20, height=20):
    return QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)


def add_items_to_grid(gridLayout, items):
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


def set_retain_size_when_hidden(widget: QtWidgets.QWidget, retain_size: bool):
    """
    Sets whether a widgets size should be retained even when it's hidden.
    """
    sp = widget.sizePolicy()
    sp.setRetainSizeWhenHidden(retain_size)
    widget.setSizePolicy(sp)


class CollapsibleFrame(QtWidgets.QFrame):
    """
    A QFrame that can be collapsed when clicked.
    """

    collapsedChanged = QtCore.Signal(bool)

    def __init__(self, parent):
        super(CollapsibleFrame, self).__init__(parent)
        self._is_collapsed = False

    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.MouseButton.LeftButton:
            self.set_is_collapsed(not self._is_collapsed)
        else:
            return super(CollapsibleFrame, self).mouseReleaseEvent(QMouseEvent)

    def set_is_collapsed(self, newCollapsed):
        """
        Set the collapsed state of this frame.
        """
        self._is_collapsed = newCollapsed
        self.collapsedChanged.emit(self._is_collapsed)

    def is_collapsed(self):
        """
        Return True if the frame is currently collapsed.
        """
        return self._is_collapsed


class RightClickMenuOnPressEventFilter(QtCore.QObject):
    """
    Handles displaying context menus on right click press instead of release.
    """

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if isinstance(event, QtGui.QMouseEvent):
            if event.button() == QtCore.Qt.RightButton:
                watched.customContextMenuRequested.emit(event.pos())
                return True
        return False
