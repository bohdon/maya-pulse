"""
Pulse

A rigging framework and toolkit built for Maya.

>>> import pulse.ui
>>> pulse.ui.show_editor_ui()

https://github.com/bohdon/maya-pulse
"""

from .version import __version__


def reload():
    """
    Perform a development reload of the Pulse python package.
    """
    import pymel.core as pm
    from .vendor import mayacoretools

    # attempt to tear down ui if it's up
    is_ui_showing = False
    try:
        from . import ui

        is_ui_showing = ui.is_editor_ui_showing()
        ui.tear_down_ui()
    except:
        pass

    # flush any pulse commands that may be in the undo queue
    pm.flushUndo()
    # unload the pulse commands plugin
    pm.unloadPlugin("pulse", force=True)

    try:
        ui.destroy_ui_model_instances()
    except:
        pass

    # delete all pulse modules from sys
    mayacoretools.deleteModules("pulse*")

    from .ui import show_editor_ui, menu

    menu.install_main_menu()

    if is_ui_showing:
        pm.evalDeferred(show_editor_ui)
