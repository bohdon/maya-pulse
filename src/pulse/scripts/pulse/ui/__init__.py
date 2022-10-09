from . import core
from . import pulseeditor
from .gen import resources_rc
from .contextmenus import unregisterContextMenu, registerContextMenu


def toggleEditorUI():
    pulseeditor.PulseEditorWindow.toggleWindow()


def showEditorUI(enableContextMenus=True):
    pulseeditor.PulseEditorWindow.showWindow()
    if enableContextMenus:
        registerContextMenu()


def hideEditorUI():
    pulseeditor.PulseEditorWindow.hideWindow()


def tearDownUI():
    """
    Hide and delete UI elements and registered callbacks.
    Intended for development reloading purposes.
    """
    hideEditorUI()
    destroyAllPulseWindows()
    destroyUIModelInstances()
    unregisterContextMenu()
    resources_rc.qCleanupResources()


def destroyAllPulseWindows():
    """
    Destroy all PulseWindows and their workspace controls.
    Intended for development reloading purposes.
    """
    for cls in core.PulseWindow.__subclasses__():
        cls.destroyWindow()


def destroyUIModelInstances():
    """
    Destroy all BlueprintUIModel instances, and
    unregister any scene callbacks.
    """
    core.BlueprintUIModel.deleteAllSharedModels()
