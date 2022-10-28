"""
Menus that can be installed into the Maya UI for quickly launching Pulse.
"""
import webbrowser

import pymel.core as pm

MAIN_MENU_LABEL = 'Pulse'
MAIN_MENU_ID = 'pulse_main_menu'
DOCUMENTATION_URL = 'https://maya-pulse.readthedocs.io/'
ISSUES_URL = 'https://github.com/bohdon/maya-pulse/issues'


def _cmd(command):
    """
    Command wrapper that accepts any amount of arguments.
    """

    def _callback(*args, **kwargs):
        command()

    return _callback


def _url_cmd(url):
    def _callback(*args, **kwargs):
        webbrowser.open(url)

    return _callback


def install_main_menu():
    """
    Install the top-level Pulse menu.
    """
    from .. import reload
    from . import toggle_editor_ui
    from .actioneditor import ActionEditorWindow
    from .actionpalette import ActionPaletteWindow
    from .actiontree import ActionTreeWindow
    from .designtoolkit import DesignToolkitWindow
    from .main_settings import MainSettingsWindow

    _create_menu(MAIN_MENU_LABEL, MAIN_MENU_ID)

    pm.menuItem(parent=MAIN_MENU_ID, label="Editors", divider=True)
    pm.menuItem(parent=MAIN_MENU_ID, label="Pulse Editor", command=_cmd(toggle_editor_ui))
    pm.menuItem(parent=MAIN_MENU_ID, label="Design Toolkit", command=_cmd(DesignToolkitWindow.toggleWindow))
    pm.menuItem(parent=MAIN_MENU_ID, label="Action Editor", command=_cmd(ActionEditorWindow.toggleWindow))
    pm.menuItem(parent=MAIN_MENU_ID, label="Action Palette", command=_cmd(ActionPaletteWindow.toggleWindow))
    pm.menuItem(parent=MAIN_MENU_ID, label="Action Tree", command=_cmd(ActionTreeWindow.toggleWindow))

    pm.menuItem(parent=MAIN_MENU_ID, label="Settings", divider=True)
    pm.menuItem(parent=MAIN_MENU_ID, label="Settings", command=_cmd(MainSettingsWindow.toggleWindow))

    pm.menuItem(parent=MAIN_MENU_ID, label="Utils", divider=True)
    pm.menuItem(parent=MAIN_MENU_ID, label="Reload", command=_cmd(reload))

    pm.menuItem(parent=MAIN_MENU_ID, label="Help", divider=True)
    pm.menuItem(parent=MAIN_MENU_ID, label="Documentation", command=_url_cmd(DOCUMENTATION_URL))
    pm.menuItem(parent=MAIN_MENU_ID, label="Report an Issue...", command=_url_cmd(ISSUES_URL))


def _create_menu(label: str, menu_id: str):
    """
    Create or recreate a menu attached to the main Maya window.

    Args:
        label: The display name of the menu.
        menu_id: The id of the menu.
    """
    # delete menu if it exists
    if pm.menu(menu_id, exists=True):
        pm.deleteUI(menu_id)

    pm.menu(menu_id, parent='MayaWindow', tearOff=True, allowOptionBoxes=True, label=label)
