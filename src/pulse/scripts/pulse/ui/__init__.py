"""
The main package containing all UI and menu functionality.
"""


def toggle_editor_ui():
    from .main_editor import MainEditorWindow

    MainEditorWindow.toggleWindow()


def show_editor_ui(enable_context_menus=True):
    from .main_editor import MainEditorWindow
    from .contextmenus import registerContextMenu

    MainEditorWindow.showWindow()
    if enable_context_menus:
        registerContextMenu()


def hide_editor_ui():
    from .main_editor import MainEditorWindow

    MainEditorWindow.hideWindow()


def is_editor_ui_showing() -> bool:
    from .main_editor import MainEditorWindow

    return MainEditorWindow.isRaised()


def tear_down_ui():
    """
    Hide and delete UI elements and registered callbacks.
    Intended for development reloading purposes.
    """
    from .gen import icons_rc
    from .contextmenus import unregisterContextMenu

    hide_editor_ui()
    destroy_all_pulse_windows()
    destroy_ui_model_instances()
    unregisterContextMenu()
    icons_rc.qCleanupResources()


def destroy_all_pulse_windows():
    """
    Destroy all PulseWindows and their workspace controls.
    Intended for development reloading purposes.
    """
    from .core import PulseWindow

    for cls in PulseWindow.__subclasses__():
        cls.destroyWindow()


def destroy_ui_model_instances():
    """
    Destroy all BlueprintUIModel instances, and
    unregister any scene callbacks.
    """
    from .core import BlueprintUIModel

    BlueprintUIModel.deleteAllSharedModels()
