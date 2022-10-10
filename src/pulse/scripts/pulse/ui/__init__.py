from . import core
from .main_editor import MainEditorWindow
from .gen import resources_rc
from .contextmenus import unregisterContextMenu, registerContextMenu


def toggle_editor_ui():
    MainEditorWindow.toggleWindow()


def show_editor_ui(enable_context_menus=True):
    MainEditorWindow.showWindow()
    if enable_context_menus:
        registerContextMenu()


def hide_editor_ui():
    MainEditorWindow.hideWindow()


def tear_down_ui():
    """
    Hide and delete UI elements and registered callbacks.
    Intended for development reloading purposes.
    """
    hide_editor_ui()
    destroy_all_pulse_windows()
    destroy_ui_model_instances()
    unregisterContextMenu()
    resources_rc.qCleanupResources()


def destroy_all_pulse_windows():
    """
    Destroy all PulseWindows and their workspace controls.
    Intended for development reloading purposes.
    """
    for cls in core.PulseWindow.__subclasses__():
        cls.destroyWindow()


def destroy_ui_model_instances():
    """
    Destroy all BlueprintUIModel instances, and
    unregister any scene callbacks.
    """
    core.BlueprintUIModel.deleteAllSharedModels()
