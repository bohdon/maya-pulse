import logging

import pymel.core as pm
from maya import cmds

from .vendor import pymetanode as meta
from .cameras import save_cameras, restore_cameras

LOG = logging.getLogger(__name__)

RIG_METACLASS = "pulse_rig"


def is_rig(node):
    """
    Return whether a node represents a pulse rig

    Args:
        node: A PyNode or string node name
    """
    return meta.hasMetaClass(node, RIG_METACLASS)


def get_all_rigs():
    """
    Return a list of all rigs in the scene
    """
    return meta.findMetaNodes(RIG_METACLASS)


def get_all_rigs_by_name(names):
    """
    Return a list of all rigs in the scene that
    have a specific rig name

    Args:
        names: A list of string rig names
    """
    rigs = get_all_rigs()
    matches = []
    for r in rigs:
        data = meta.getMetaData(r, RIG_METACLASS)
        if data.get("name") in names:
            matches.append(r)
    return matches


def get_rig_from_node(node):
    """
    Return the rig that owns this node, if any

    Args:
        node: A PyNode rig or node that is part of a rig
    """
    if is_rig(node):
        return node
    else:
        parent = node.getParent()
        if parent:
            return get_rig_from_node(parent)


def get_selected_rigs():
    """
    Return the selected rigs
    """
    rigs = list(set([get_rig_from_node(s) for s in pm.selected()]))
    rigs = [r for r in rigs if r is not None]
    return rigs


def create_rig_node(name: str) -> pm.nt.Transform:
    """
    Create and return a new Rig node

    Args:
        name: A str name of the rig
    """
    if cmds.objExists(name):
        raise ValueError(f"Cannot create rig, node already exists: {name}")
    node = pm.group(name=name, em=True)
    for a in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
        node.attr(a).setLocked(True)
        node.attr(a).setKeyable(False)
    # set initial metadata for the rig
    meta.setMetaData(node, RIG_METACLASS, {"name": name})
    return node


def open_rig_blueprint(rig):
    """
    Open the Blueprint source file that was used
    to build a rig.

    Args:
        rig: A rig node
    """

    rig_data = meta.getMetaData(rig, RIG_METACLASS)
    blueprint_file = rig_data.get("blueprintFile")
    if not blueprint_file:
        LOG.warning("No blueprintFile set on the rig")
        return

    LOG.info("Opening blueprint: %s", blueprint_file)
    save_cameras()
    pm.openFile(blueprint_file, f=True)
    restore_cameras()


def open_first_rig_blueprint():
    rigs = get_all_rigs()
    if not rigs:
        LOG.warning("No rig in the scene")
        return
    open_rig_blueprint(rigs[0])


class Rig(object):
    """
    A wrapper for rig transform nodes that allows easy access to rig metadata.
    """

    def __init__(self, node):
        if not is_rig(node):
            raise ValueError("%s is not a valid pulse rig node" % node)
        self.node = node
        self._metaData = None

    @property
    def meta_data(self):
        if self._metaData is None:
            self._metaData = meta.getMetaData(self.node, RIG_METACLASS)
        return self._metaData if self._metaData else {}

    def get_meta_data_value(self, key, default=None):
        meta_data = self.meta_data
        return meta_data.get(key, default)

    def get_core_hierarchy_node(self, name):
        """
        Return a core hierarchy transform node in the rig by name.

        Args:
            name (str): The name of the core hierarchy node as defined in the Build Core Hierarchy action
        """
        children = self.node.getChildren(type="transform")
        for child in children:
            if child.nodeName() == name:
                return child

    def get_core_hierarchy_nodes(self):
        """
        Return all core hierarchy transform nodes in the rig.
        """
        return self.node.getChildren(type="transform")

    def get_anim_controls(self):
        """
        Return all animation controls in the rig.
        """
        return self.get_meta_data_value("animControls", [])

    def get_render_geo(self):
        """
        Return all geometry that has been added to the rigs 'renderGeo' metadata.
        """
        return self.get_meta_data_value("renderGeo", [])

    def get_bake_nodes(self):
        """
        Return all nodes that have been added to the 'bakeNodes' metadata.
        """
        return self.get_meta_data_value("bakeNodes", [])

    def get_spaces(self):
        """
        Return a dict of all spaces and corresponding space nodes.
        """
        return self.get_meta_data_value("spaces", {})
