
import maya.cmds as cmds

from .core import *
from .actionattrform import *
from .actioneditor import *
from .actionpalette import *
from .actiontree import *
from .buildtoolbar import *
from .manageview import *
from .pulseeditor import *
from .quickcolor import *
from .quickname import *


def toggleEditorUI():
    PulseEditorWindow.toggleWindow()


def showEditorUI():
    PulseEditorWindow.showWindow()


def hideEditorUI():
    PulseEditorWindow.hideWindow()


def tearDownUI():
    """
    Hide and delete UI elements and registered callbacks.
    """
    hideEditorUI()
    destroyEditorWorkspaceControls()


def destroyEditorWorkspaceControls():
    """
    Development util to destroy workspace controls
    for all PulseWindows. Not intended for normal usage.
    """
    import designviews
    designviews.destroyEditorWorkspaceControls()

    ActionEditorWindow.destroyWindow()
    ActionTreeWindow.destroyWindow()
    PulseEditorWindow.destroyWindow()
    QuickNameWindow.destroyWindow()
    QuickColorWindow.destroyWindow()


def destroyUIModelInstances():
    """
    Destroy all BlueprintUIModel instances, and
    unregister any scene callbacks.
    """
    BlueprintUIModel.deleteAllSharedModels()
