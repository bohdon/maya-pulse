
import maya.cmds as cmds

from .core import *
from .actionattrform import *
from .actioneditor import *
from .actiontree import *
from .blueprinteditor import *
from .buildtoolbar import *
from .pulseeditor import *
from .quickname import *
from .quickcolor import *


def toggleEditorUI():
    PulseEditorWindow.toggleWindow()


def showEditorUI():
    PulseEditorWindow.showWindow()


def hideEditorUI():
    PulseEditorWindow.hideWindow()


def destroyEditorWorkspaceControls():
    """
    Development util to destroy workspace controls
    for all PulseWindows. Not intended for normal usage.
    """
    import designviews
    designviews.destroyEditorWorkspaceControls()

    ActionEditorWindow.destroyWindow()
    ActionTreeWindow.destroyWindow()
    BlueprintEditorWindow.destroyWindow()
    BuildToolbarWindow.destroyWindow()
    PulseEditorWindow.destroyWindow()
    QuickNameWindow.destroyWindow()
    QuickColorWindow.destroyWindow()
