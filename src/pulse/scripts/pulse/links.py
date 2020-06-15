"""
Links are used to ensure that nodes update to
match each others' positions when doing rig layout.

They are like parent constraints that exist without
any additional nodes or connections between nodes,
and are only updated when requested by the designer.

Link information is stored in the scene on each node
using meta data.
"""

import logging

import pymel.core as pm
import pymetanode as meta

import pulse.nodes

__all__ = [
    'cleanupLinks',
    'clearLinkOffsets',
    'getAllLinkedNodes',
    'getLink',
    'getLinkMetaData',
    'link',
    'positionLink',
    'saveLinkOffsets',
    'unlink',
]

LOG = logging.getLogger(__name__)

LINK_METACLASS = 'pulse_link'

# map of link types to positioner classes
POSITIONER_CLASS_MAP = {}


class LinkType(object):
    # the linked object will follow the target's position
    DEFAULT = 'default'
    # the linked object will be placed automatically
    # based on an ik pole vector, and target distance
    IKPOLE = 'ikpole'


def link(leader, follower, linkType=LinkType.DEFAULT, **kwargs):
    """
    Link the follower to a leader
    """
    linkData = {
        'targetNode': leader,
        'type': linkType,
    }
    linkData.update(kwargs)
    setLinkMetaData(follower, linkData)
    LOG.info("Linked %s to %s (linkType: %s)", follower, leader, linkType)


def saveLinkOffsets(node, offsetTranslate=True, offsetRotate=True, offsetScale=False):
    """
    Save the current offset of a linked node in relation to its target node.
    """
    precision = 5

    # get link meta data
    linkData = getLinkMetaData(node)
    targetNode = linkData.get('targetNode')
    if targetNode:
        # get local matrix of follower relative to leader
        offsetMtx = pm.dt.TransformationMatrix(node.wm.get() * targetNode.wim.get())
        # initialize variables for logging later
        tOffset = rOffset = sOffset = None
        if offsetTranslate:
            tOffset = [round(v, precision) for v in offsetMtx.getTranslation('world')]
            linkData['offsetTranslate'] = tOffset
        if offsetRotate:
            rot = offsetMtx.getRotation()
            rot.setDisplayUnit('degrees')
            rOffset = [round(v, precision) for v in rot]
            linkData['offsetRotate'] = rOffset
        if offsetScale:
            sOffset = [round(v, precision) for v in offsetMtx.getScale('world')]
            linkData['offsetScale'] = sOffset
        setLinkMetaData(node, linkData)
        LOG.info("Set link offsets: %s (translate: %s, rotate: %s, scale: %s)", node, tOffset, rOffset, sOffset)


def clearLinkOffsets(node, offsetTranslate=True, offsetRotate=True, offsetScale=True):
    """
    Clear the transform offsets for a linked node.

    Args:
        offsetTranslate (bool): If true, clear translate offsets
        offsetRotate (bool): If true, clear rotate offsets
        offsetScale (bool): If true, clear scale offsets
    """
    # get link meta data
    linkData = getLinkMetaData(node)

    # delete offset data
    didChange = False
    if offsetTranslate and 'offsetTranslate' in linkData:
        del linkData['offsetTranslate']
        didChange = True
    if offsetRotate and 'offsetRotate' in linkData:
        del linkData['offsetRotate']
        didChange = True
    if offsetScale and 'offsetScale' in linkData:
        del linkData['offsetScale']
        didChange = True

    if didChange:
        # update meta data
        setLinkMetaData(node, linkData)


def unlink(node):
    """
    Remove a link from a node
    """
    meta.removeMetaData(node, className=LINK_METACLASS)
    LOG.info("Unlinked %s", node)


def isLinked(node):
    return meta.hasMetaClass(node, className=LINK_METACLASS)


def getLink(node):
    """
    Return the leader that a node is linked to
    """
    metaData = getLinkMetaData(node)
    return metaData.get('targetNode')


def getLinkMetaData(node):
    """
    Return all link metadata for a node
    """
    result = meta.getMetaData(node, className=LINK_METACLASS)
    if not result:
        return {}

    # support legacy data of just a target node
    if isinstance(result, pm.PyNode):
        return {'targetNode': result}

    return result


def setLinkMetaData(node, linkData):
    """
    Set the metadata for a linked node
    """
    if not 'targetNode' in linkData:
        raise ValueError("LinkData must contain a `targetNode`")
    meta.setMetaData(node, className=LINK_METACLASS, data=linkData)


def getAllLinkedNodes():
    """
    Return all nodes in the scene that are linked
    """
    return meta.findMetaNodes(className=LINK_METACLASS)


def cleanupLinks():
    """
    Cleanup all nodes in the scene that have broken links
    """
    nodes = meta.findMetaNodes(className=LINK_METACLASS)
    for node in nodes:
        if not getLink(node):
            unlink(node)


def positionLink(node, translate=True, rotate=True, scale=False, quiet=False):
    linkData = getLinkMetaData(node)

    if not linkData:
        if not quiet:
            LOG.warning("Node is not linked to anything: %s", node)
        return

    # get target node
    leader = linkData.get('targetNode')
    if not leader:
        if not quiet:
            LOG.warning("Linked node has no target: %s", node)
        return

    # get positioner class by link type
    linkType = linkData.get('type', LinkType.DEFAULT)
    positionerCls = POSITIONER_CLASS_MAP.get(linkType)
    if not positionerCls:
        raise ValueError("Could not find a LinkPositioner for type: %s" % linkType)

    positioner = positionerCls()
    positioner.shouldTranslate = translate
    positioner.shouldRotate = rotate
    positioner.shouldScale = scale
    positioner.updateTransform(leader, node, linkData)


class LinkPositioner(object):
    """
    Handles updating the transform of a linked object
    to match its target.
    """

    def __init__(self):
        self.shouldTranslate = True
        self.shouldRotate = True
        self.shouldScale = False

    def getOffsetMatrix(self, linkData):
        """
        Return the offset matrix to apply using any offsets
        defined in the link's meta data.
        """
        tOffset = linkData.get('offsetTranslate')
        rOffset = linkData.get('offsetRotate')
        sOffset = linkData.get('offsetScale')
        mtx = pm.dt.TransformationMatrix()
        if sOffset:
            mtx.setScale(sOffset, 'world')
        if rOffset:
            mtx.setRotation(rOffset)
        if tOffset:
            mtx.setTranslation(tOffset, 'world')
        return mtx

    def updateTransform(self, leader, follower, linkData):
        """
        Update the transform of follower based on leader
        """
        raise NotImplementedError


class DefaultLinkPositioner(LinkPositioner):
    """
    Default positioner, updates the follower to match the
    leaders position, with optional offsets.
    """

    def updateTransform(self, leader, follower, linkData):
        worldMtx = pulse.nodes.getWorldMatrix(leader)
        offsetMtx = self.getOffsetMatrix(linkData)
        newMtx = offsetMtx * worldMtx
        pulse.nodes.setWorldMatrix(
            follower, newMtx,
            translate=self.shouldTranslate,
            rotate=self.shouldRotate,
            scale=self.shouldScale)


POSITIONER_CLASS_MAP[LinkType.DEFAULT] = DefaultLinkPositioner


class IKPoleLinkPositioner(LinkPositioner):
    """
    IK Pole positioner, updates the follower to be placed
    along the pole vector.
    """

    def updateTransform(self, leader, follower, linkData):
        poleVector, midPoint = pulse.joints.getIKPoleVectorAndMidPoint(leader)

        distance = linkData.get('ikpoleDistance')
        if not distance:
            # calculate distance based on followers current location
            midToFollowerVector = follower.getTranslation(space='world') - midPoint
            distance = poleVector.dot(midToFollowerVector)

        newTranslate = midPoint + poleVector * distance
        follower.setTranslation(newTranslate, space='world')


POSITIONER_CLASS_MAP[LinkType.IKPOLE] = IKPoleLinkPositioner
