"""
Menus that can be installed into the Maya UI for quickly launching Pulse.
"""
import pymel.core as pm

MAIN_MENU_LABEL = 'Pulse'
MAIN_MENU_ID = 'pulse_main_menu'


def install_main_menu():
    """
    Install the top-level Pulse menu.
    """
    _create_menu(MAIN_MENU_LABEL, MAIN_MENU_ID)

    toggle_cmd = "import pulse.ui;pulse.ui.toggle_editor_ui()"
    pm.menuItem(parent=MAIN_MENU_ID, label="Show Pulse UI", command=toggle_cmd)


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
