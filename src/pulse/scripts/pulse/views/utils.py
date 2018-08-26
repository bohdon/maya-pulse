
import os
import logging
from functools import partial, wraps
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import maya.cmds as cmds


__all__ = [
    'clearLayout',
    'dpiScale',
    'getIcon',
    'getIconPath',
    'getIconPixmap',
    'repeatable',
    'repeatPartial',
    'undoable',
    'undoAndRepeatable',
    'undoAndRepeatPartial',
    'undoPartial',
]

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
