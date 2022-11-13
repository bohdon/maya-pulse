"""
Menus and utils for working with blueprints or rigs.
Action context menus provides an extensible way to add features based
on the metaclass of animation controls.
"""
from typing import List, Type, Optional

import pymel.core as pm

from ..vendor import pymetanode as meta


class Object(object):
    pass


try:
    import rmbmenuhook
except ImportError:
    # create mock class so context menu classes don't error on import
    rmbmenuhook = Object()
    rmbmenuhook.Menu = object
    has_rmbmenuhook = False
else:
    has_rmbmenuhook = True

RMB_MENU_NAME = "pulseActionNodeContextMenu"


def register_context_menu(priority: int = 0):
    """
    Register pulse context menus with the right click menu.
    """
    # ensure actions are loaded, since they provide the context menu functionality
    from .. import loader

    loader.load_actions()

    if has_rmbmenuhook:
        rmbmenuhook.registerMenu(RMB_MENU_NAME, PulseNodeContextMenu, priority)


def unregister_context_menu():
    """
    Unregister the pulse context menu
    """
    if has_rmbmenuhook:
        rmbmenuhook.unregisterMenu(RMB_MENU_NAME)


def can_register_context_menus() -> bool:
    return has_rmbmenuhook


class PulseNodeContextMenu(rmbmenuhook.Menu):
    """
    Right click context menu that is shown for any nodes with available sub menus.
    Subclass ActionNodeContextSubMenu to add a submenu.

    self.hitNode (pm.PyNode): The last selected node, or node under the mouse pointer
    """

    def __init__(self, menu, obj=None):
        super().__init__(menu, obj)

        self.hitNode = pm.PyNode(self.object) if self.object else None

        self.submenu_classes = self.get_sub_menu_classes()

    def get_sub_menu_classes(self) -> List[Type["PulseNodeContextSubMenu"]]:
        """
        Return a list of BuildActionContextMenuItem classes available for a node
        """
        result = []
        for subclass in PulseNodeContextSubMenu.__subclasses__():
            if subclass.should_build_sub_menu(self):
                result.append(subclass)
        return result

    def shouldBuild(self) -> bool:
        return bool(self.submenu_classes)

    def build(self):
        pm.setParent(self.menu, m=True)

        num_submenus = len(self.submenu_classes)
        for submenu_class in self.submenu_classes:
            submenu = submenu_class(self, num_submenus == 1)
            submenu.build_menu_items()

    def is_radial_position_occupied(self, radial_position: str):
        """
        Return true if a radial position is currently occupied by an existing menu item.
        """
        if not radial_position:
            return False

        menu_items = pm.menu(self.menu, q=True, itemArray=True)
        for menu_item in menu_items:
            if pm.menuItem(menu_item, q=True, radialPosition=True) == radial_position:
                return True
        return False

    def get_safe_radial_position(self, radial_position: str) -> Optional[str]:
        """
        Return the given radial position if it is not already occupied, or None if it is
        """
        if self.is_radial_position_occupied(radial_position):
            return None
        return radial_position


class PulseNodeContextSubMenu(object):
    """
    Base class for a subset of menu items to add to a context menu for a node.
    Metaclasses are used to determine which menu items are available.
    """

    @classmethod
    def should_build_sub_menu(cls, menu: PulseNodeContextMenu) -> bool:
        """
        Return true if this submenu should be built for a node

        Args:
            menu (PulseNodeContextMenu): The parent context menu, containing a reference to the hit node
        """
        return False

    def __init__(self, menu: PulseNodeContextMenu, is_only_submenu: bool):
        """
        Args:
            menu: The context menu containing this submenu
            is_only_submenu: If true, this is the only submenu being shown
        """
        self.menu = menu
        self.isOnlySubmenu = is_only_submenu

    @property
    def node(self):
        return self.menu.hitNode

    def build_menu_items(self):
        """
        Build the menu items for this utility
        """
        pass

    def is_radial_position_occupied(self, radial_position: str):
        """
        Return true if a radial position is currently occupied by an existing menu item.
        """
        return self.menu.is_radial_position_occupied(radial_position)

    def get_safe_radial_position(self, radial_position: str) -> str:
        """
        Return the given radial position if it is not already occupied, or None if it is
        """
        return self.menu.get_safe_radial_position(radial_position)

    @staticmethod
    def is_node_with_metaclass_selected(*meta_class_names: str) -> bool:
        """
        Return True if any node exists in the selection with one of the given metaclasses.
        """

        def _has_any_metaclass(node, metaclass_names):
            for metaClassName in metaclass_names:
                if meta.has_metaclass(node, metaClassName):
                    return True
            return False

        for s in pm.selected(type="transform"):
            if _has_any_metaclass(s, meta_class_names):
                return True
        return False

    @staticmethod
    def get_selected_nodes_with_meta_class(*metaclass_names: str) -> List[pm.PyNode]:
        """
        Return all selected nodes that have any of the given metaclasses.
        """

        def has_any_metaclass(node, metaclass_names):
            for metaClassName in metaclass_names:
                if meta.has_metaclass(node, metaClassName):
                    return True
            return False

        return [s for s in pm.selected(type="transform") if has_any_metaclass(s, metaclass_names)]
