import logging

import pymel.core as pm
from maya import cmds

from .vendor import pymetanode as meta
from .cameras import saveCameras, restoreCameras

LOG = logging.getLogger(__name__)

RIG_METACLASS = 'pulse_rig'


def isRig(node):
    """
    Return whether a node represents a pulse rig

    Args:
        node: A PyNode or string node name
    """
    return meta.hasMetaClass(node, RIG_METACLASS)


def getAllRigs():
    """
    Return a list of all rigs in the scene
    """
    return meta.findMetaNodes(RIG_METACLASS)


def getAllRigsByName(names):
    """
    Return a list of all rigs in the scene that
    have a specific rig name

    Args:
        names: A list of string rig names
    """
    rigs = getAllRigs()
    matches = []
    for r in rigs:
        data = meta.getMetaData(r, RIG_METACLASS)
        if data.get('name') in names:
            matches.append(r)
    return matches


def getRigFromNode(node):
    """
    Return the rig that owns this node, if any

    Args:
        node: A PyNode rig or node that is part of a rig
    """
    if isRig(node):
        return node
    else:
        parent = node.getParent()
        if parent:
            return getRigFromNode(parent)


def getSelectedRigs():
    """
    Return the selected rigs
    """
    rigs = list(set([getRigFromNode(s) for s in pm.selected()]))
    rigs = [r for r in rigs if r is not None]
    return rigs


def createRigNode(name: str) -> pm.nt.Transform:
    """
    Create and return a new Rig node

    Args:
        name: A str name of the rig
    """
    if cmds.objExists(name):
        raise ValueError(f"Cannot create rig, node already exists: {name}")
    node = pm.group(name=name, em=True)
    for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
        node.attr(a).setLocked(True)
        node.attr(a).setKeyable(False)
    # set initial metadata for the rig
    meta.setMetaData(node, RIG_METACLASS, {'name': name})
    return node


def openRigBlueprint(rig):
    """
    Open the Blueprint source file that was used
    to build a rig.

    Args:
        rig: A rig node
    """

    rigdata = meta.getMetaData(rig, RIG_METACLASS)
    blueprintFile = rigdata.get('blueprintFile')
    if not blueprintFile:
        LOG.warning('No blueprintFile set on the rig')
        return

    LOG.info('Opening blueprint: ' + blueprintFile)
    saveCameras()
    pm.openFile(blueprintFile, f=True)
    restoreCameras()


def openFirstRigBlueprint():
    rigs = getAllRigs()
    if not rigs:
        LOG.warning('No rig in the scene')
        return
    openRigBlueprint(rigs[0])


class Rig(object):
    """
    A wrapper for rig transform nodes that allows easy access to rig meta data.
    """

    def __init__(self, node):
        if not isRig(node):
            raise ValueError("%s is not a valid pulse rig node" % node)
        self.node = node
        self._metaData = None

    @property
    def metaData(self):
        if self._metaData is None:
            self._metaData = meta.getMetaData(self.node, RIG_METACLASS)
        return self._metaData if self._metaData else {}

    def getMetaDataValue(self, key, default=None):
        metaData = self.metaData
        return metaData.get(key, default)

    def getCoreHierarchyNode(self, name):
        """
        Return a core hierarchy transform node in the rig by name

        Args:
            name (str): The name of the core hierarchy node as defined in the Build Core Hierarchy action
        """
        children = self.node.getChildren(type='transform')
        for child in children:
            if child.nodeName() == name:
                return child

    def getCoreHierarchyNodes(self):
        """
        Return all core hierarchy transform nodes in the rig.
        """
        return self.node.getChildren(type='transform')

    def getAnimControls(self):
        """
        Return all animation controls in the rig
        """
        return self.getMetaDataValue('animControls', [])

    def getRenderGeo(self):
        """
        Return all geometry that has been added to the rigs 'renderGeo' meta data
        """
        return self.getMetaDataValue('renderGeo', [])

    def getBakeNodes(self):
        """
        Return all nodes that have been added to the 'bakeNodes' meta data
        """
        return self.getMetaDataValue('bakeNodes', [])

    def getSpaces(self):
        """
        Return a dict of all spaces and corresponding space nodes
        """
        return self.getMetaDataValue('spaces', {})
