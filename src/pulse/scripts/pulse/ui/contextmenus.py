"""
Menus and utils for working with blueprints or rigs.
Action context menus provides an extensible way to add features based
on the metaclass of animation controls.
"""
from typing import List, Type

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

RMB_MENU_NAME = 'pulseActionNodeContextMenu'


def registerContextMenu(priority: int = 0):
    """
    Register pulse context menus with the right click menu.
    """
    if has_rmbmenuhook:
        rmbmenuhook.registerMenu(RMB_MENU_NAME, PulseNodeContextMenu, priority)


def unregisterContextMenu():
    """
    Unregister the pulse context menu
    """
    if has_rmbmenuhook:
        rmbmenuhook.unregisterMenu(RMB_MENU_NAME)


class PulseNodeContextMenu(rmbmenuhook.Menu):
    """
    Right click context menu that is shown for any nodes with available sub menus.
    Subclass ActionNodeContextSubMenu to add a submenu.

    self.hitNode (pm.PyNode): The last selected node, or node under the mouse pointer
    """

    def __init__(self, menu, obj=None):
        super().__init__(menu, obj)

        self.hitNode = pm.PyNode(self.object) if self.object else None

        self.submenu_classes = self.getSubMenuClasses()

    def getSubMenuClasses(self) -> List[Type['PulseNodeContextSubMenu']]:
        """
        Return a list of BuildActionContextMenuItem classes available for a node
        """
        result = []
        for subclass in PulseNodeContextSubMenu.__subclasses__():
            if subclass.shouldBuildSubMenu(self):
                result.append(subclass)
        return result

    def shouldBuild(self) -> bool:
        return bool(self.submenu_classes)

    def build(self):
        pm.setParent(self.menu, m=True)

        num_submenus = len(self.submenu_classes)
        for submenu_class in self.submenu_classes:
            submenu = submenu_class(self, num_submenus == 1)
            submenu.buildMenuItems()

    def isRadialPositionOccupied(self, radialPosition: str):
        """
        Return true if a radial position is currently occupied by an existing menu item.
        """
        if not radialPosition:
            return False

        menu_items = pm.menu(self.menu, q=True, itemArray=True)
        for menu_item in menu_items:
            if pm.menuItem(menu_item, q=True, radialPosition=True) == radialPosition:
                return True
        return False

    def getSafeRadialPosition(self, radialPosition: str) -> str:
        """
        Return the given radial position if it is not already occupied, or None if it is
        """
        if self.isRadialPositionOccupied(radialPosition):
            return None
        return radialPosition


class PulseNodeContextSubMenu(object):
    """
    Base class for a subset of menu items to add to a context menu for a node.
    Meta classes are used to determine which menu items are available.
    """

    @classmethod
    def shouldBuildSubMenu(cls, menu: PulseNodeContextMenu) -> bool:
        """
        Return true if this submenu should be built for a node

        Args:
            menu (PulseNodeContextMenu): The parent context menu, containing a reference to the hit node
        """
        return False

    def __init__(self, menu: PulseNodeContextMenu, isOnlySubmenu: bool):
        """
        Args:
            menu: The context menu containing this submenu
            isOnlySubmenu: If true, this is the only submenu being shown
        """
        self.menu = menu
        self.isOnlySubmenu = isOnlySubmenu

    @property
    def node(self):
        return self.menu.hitNode

    def buildMenuItems(self):
        """
        Build the menu items for this utility
        """
        pass

    def isRadialPositionOccupied(self, radialPosition: str):
        """
        Return true if a radial position is currently occupied by an existing menu item.
        """
        return self.menu.isRadialPositionOccupied(radialPosition)

    def getSafeRadialPosition(self, radialPosition: str) -> str:
        """
        Return the given radial position if it is not already occupied, or None if it is
        """
        return self.menu.getSafeRadialPosition(radialPosition)

    @staticmethod
    def isNodeWithMetaClassSelected(*metaClassNames: str) -> bool:
        """
        Return True if any node exists in the selection with one of the given meta classes
        """

        def hasAnyMetaClass(node, metaClassNames):
            for metaClassName in metaClassNames:
                if meta.hasMetaClass(node, metaClassName):
                    return True
            return False

        for s in pm.selected(type='transform'):
            if hasAnyMetaClass(s, metaClassNames):
                return True
        return False

    @staticmethod
    def getSelectedNodesWithMetaClass(*metaClassNames: str) -> List[pm.PyNode]:
        """
        Return all selected nodes that have any of the given meta classes
        """

        def hasAnyMetaClass(node, metaClassNames):
            for metaClassName in metaClassNames:
                if meta.hasMetaClass(node, metaClassName):
                    return True
            return False

        return [s for s in pm.selected(type='transform') if hasAnyMetaClass(s, metaClassNames)]
