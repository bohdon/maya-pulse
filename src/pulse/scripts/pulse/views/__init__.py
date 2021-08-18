from . import actioneditor
from . import actiontree
from . import core
from . import designview
from . import pulseeditor
from . import quickcolor
from . import quickname
from .core import PulseWindow


def toggleEditorUI():
    pulseeditor.PulseEditorWindow.toggleWindow()


def showEditorUI():
    pulseeditor.PulseEditorWindow.showWindow()


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


def destroyAllPulseWindows():
    """
    Destroy all PulseWindows and their workspace controls.
    Intended for development reloading purposes.
    """
    for cls in PulseWindow.__subclasses__():
        cls.destroyWindow()


def destroyUIModelInstances():
    """
    Destroy all BlueprintUIModel instances, and
    unregister any scene callbacks.
    """
    core.BlueprintUIModel.deleteAllSharedModels()
