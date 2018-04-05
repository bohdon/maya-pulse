"""
Symmetry Tools

There are two types of mirroring used here:

Simple Mirror:
    a ctl is mirrored across a single axis in the tranditional
    sense, this means the non-mirror axis basis vectors are flipped

Aligned Mirror:
    a ctl is mirrored across a single axis in a visual sense,
    but the relationship between the matrices is more complicated.
    The result is an orientation that looks the same on both
    sides of an axis, as if they matched in world space in rest pose

"""

import logging
import pymel.core as pm
import pymetanode as meta

from . import nodes

__all__ = [
    'getAllMirrorNodes',
    'getOtherMirrorNode',
    'isCentered',
    'isMirrorNode',
    'removeMirroringData',
    'setMirroringData',
    'validateMirrorNode',
]

LOG = logging.getLogger(__name__)

MIRROR_METACLASS = 'pulse_mirror'
MIRROR_THRESHOLD = 0.0001

MIRRORMODE_SIMPLE = 'simple'
MIRRORMODE_ALIGNED = 'aligned'


# Nodes
# -----

def getAllMirrorNodes():
    """
    Return all nodes that have mirroring data
    """
    return meta.findMetaNodes(MIRROR_METACLASS)


def isMirrorNode(node):
    """
    Return whether a node has mirroring data

    Args:
        node: A PyNode, MObject, or node name
    """
    return meta.hasMetaClass(node, MIRROR_METACLASS)


def validateMirrorNode(node):
    """
    Ensure the node still has a valid mirroring counterpart.
    If it does not, remove the mirror data from the node.

    Return:
        True if the node is a valid mirror node
    """
    if not isMirrorNode(node):
        return False
    data = meta.getMetaData(node, MIRROR_METACLASS)
    otherNode = data['otherNode']
    if otherNode is None:
        LOG.debug('{0} had empty mirrorNode, removing mirroring data'.format(node))
        meta.removeMetaData(node, MIRROR_METACLASS)
        return False
    return True


def cleanupAllMirrorNodes():
    """
    Remove mirroring meta data from any nodes in the scene
    that are no longer valid (missing their counterpart node).
    """
    for node in getAllMirrorNodes():
        validateMirrorNode(node)


def pairMirrorNodes(nodeA, nodeB):
    """
    Make both nodes associated as mirrors by adding
    mirroring data and a reference to each other.

    Args:
        nodeA: A PyNode, MObject, or node name
        nodeB: A PyNode, MObject, or node name
    """
    setMirroringData(nodeA, nodeB)
    setMirroringData(nodeB, nodeA)


def unpairMirrorNode(node):
    """
    Unpair the node from any associated mirror node.
    This removes mirroring data from both this
    node and its counterpart.

    Args:
        node: A PyNode, MObject, or node name
    """
    if isMirrorNode(node):
        otherNode = getOtherMirrorNode(node)
        removeMirroringData(node)
        removeMirroringData(otherNode)


def setMirroringData(node, otherNode):
    """
    Set the mirroring data for a node

    Args:
        node: A node on which to set the mirroring data
        otherNode: The counterpart node to be stored in the mirroring data
    """
    data = {
        'otherNode': otherNode,
    }
    meta.setMetaData(node, MIRROR_METACLASS, data, undoable=True)


def getOtherMirrorNode(node):
    """
    For a node with mirroring data, return the other node.

    Args:
        node: A node with mirroring data that references another node
    """
    if isMirrorNode(node):
        data = meta.getMetaData(node, MIRROR_METACLASS)
        return data['otherNode']


def removeMirroringData(node):
    """
    Remove mirroring data from a node. This does NOT
    remove mirroring data from the other node, if there
    is one. See `unpairMirrorNode` for removing mirroring
    data from two nodes at once.

    Args:
        node: A PyNode, MObject, or node name
    """
    meta.removeMetaData(node, MIRROR_METACLASS)


# Transformations
# ---------------

def isCentered(node, axis=0):
    """
    Return True if the node is centered on a specific world axis.
    """
    axis = nodes.getAxis(axis)
    return abs(node.getTranslation(space='world')[axis.index]) < MIRROR_THRESHOLD


def getCenteredParent(node, axis=0):
    """
    Return the closest parent node that is centered.
    If no parent nodes are centered, return the highest parent.

    Args:
        node: A PyNode
    """
    thisParent = node.getParent()
    if thisParent is None:
        return
    while thisParent is not None:
        if isCentered(thisParent, axis):
            return thisParent
        lastParent = thisParent
        thisParent = lastParent.getParent()
    return lastParent


def getMirroredParent(node):
    """
    Return the closest parent node that has mirroring data.

    Args:
        node: A PyNode
    """
    thisParent = node.getParent()
    if thisParent is None:
        return
    while thisParent is not None:
        if isMirrorNode(thisParent):
            return thisParent
        lastParent = thisParent
        thisParent = lastParent.getParent()
    return lastParent


def getMirroredOrCenteredParent(node, axis=0):
    """
    Return the closest parent node that is either centered,
    or already paired with another mirroring node.
    """
    center = getCenteredParent(node, axis)
    mirror = getMirroredParent(node)
    if center is None:
        return mirror
    if mirror is None:
        return center
    if center.hasParent(mirror):
        return center
    if mirror.hasParent(center):
        return mirror
    return center


def getMirrorMode(nodeA, nodeB):
    """
    Given two nodes, return the mirror mode that matches
    their current transform relationship.

    Simple performs a loose check to see if the nodes are
    aligned, and if not, returns the Simple mirroring mode.
    """
    awm = nodes.getWorldMatrix(nodeA)
    bwm = nodes.getWorldMatrix(nodeB)
    aaxes = nodes.getClosestAlignedAxes(awm)
    baxes = nodes.getClosestAlignedAxes(bwm)
    if aaxes == baxes:
        return MIRRORMODE_ALIGNED
    return MIRRORMODE_SIMPLE

