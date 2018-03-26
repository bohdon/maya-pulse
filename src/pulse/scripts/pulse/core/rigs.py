

import logging
import pymel.core as pm
import pymetanode as meta

from ..cameras import saveCameras, restoreCameras

__all__ = [
    'getAllRigs',
    'getAllRigsByName',
    'getRigFromNode',
    'getSelectedRigs',
    'isRig',
    'openFirstRigBlueprint',
    'openRigBlueprint',
    'RIG_METACLASS',
]


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


def createRigNode(name):
    """
    Create and return a new Rig node

    Args:
        name: A str name of the rig
    """
    if pm.cmds.objExists(name):
        raise ValueError(
            "Cannot create rig, node already exists: {0}".format(name))
    node = pm.group(name=name, em=True)
    for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
        node.attr(a).setLocked(True)
        node.attr(a).setKeyable(False)
    # set initial meta data for the rig
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

