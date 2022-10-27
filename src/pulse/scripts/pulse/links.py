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
import operator

import pymel.core as pm

from .vendor import pymetanode as meta
from . import joints, math
from . import nodes

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
    # the linked object will be placed at weighted position between targets
    WEIGHTED = 'weighted'


def createDefaultLink(follower, leader, keepOffset=False):
    positioner = DefaultLinkPositioner()
    positioner.keepOffset = keepOffset
    positioner.createLink(follower, [leader])


def recreateLink(node, keepOffset=False):
    """
    Recreate the link for a node, updating or removing its offsets if necessary.
    """
    linkData = getLinkMetaData(node)
    if linkData:
        positioner = getPositioner(linkData.get('type', LinkType.DEFAULT))
        positioner.keepOffset = keepOffset
        positioner.recreateLink(node, linkData)


def unlink(node):
    """
    Remove a link from a node
    """
    meta.removeMetaData(node, className=LINK_METACLASS)
    LOG.info("Unlinked %s", node)


def isLinked(node):
    return meta.hasMetaClass(node, className=LINK_METACLASS)


def getLinkedNodes(node):
    """
    Return all leaders a node is linked to.
    """
    linkData = getLinkMetaData(node)
    positioner = getPositioner(linkData.get('type', LinkType.DEFAULT))
    positioner.getTargetNodes(linkData)


def getLinkMetaData(node):
    """
    Return all link metadata for a node
    """
    result = meta.getMetaData(node, className=LINK_METACLASS)
    if not result:
        return {}

    return result


def getPositioner(linkType):
    """
    Create and return a new positioner instance for a link type.
    """
    # get positioner class by link type
    positionerCls = POSITIONER_CLASS_MAP.get(linkType)
    if not positionerCls:
        raise ValueError("Could not find a LinkPositioner for type: %s" % linkType)

    positioner = positionerCls()
    return positioner


def setLinkMetaData(node, linkData):
    """
    Set the metadata for a linked node
    """
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
    link_nodes = meta.findMetaNodes(className=LINK_METACLASS)
    for node in link_nodes:
        if not getLinkedNodes(node):
            unlink(node)


def applyLinkPosition(node, quiet=False):
    linkData = getLinkMetaData(node)

    if not linkData:
        if not quiet:
            LOG.warning("Node is not linked to anything: %s", node)
        return

    positioner = getPositioner(linkData.get('type', LinkType.DEFAULT))
    positioner.applyLinkPosition(node, linkData)


class LinkPositioner(object):
    """
    Handles updating the transform of a linked object
    to match its target.
    """

    # The unique name of the link type represented by this positioner.
    linkType = None

    def __init__(self):
        # if true, maintain the followers current offset when creating a link
        self.keepOffset = False

    def setLinkMetaData(self, node, linkData):
        """
        Set the metadata for a linked node
        """
        linkData['type'] = self.linkType
        meta.setMetaData(node, className=LINK_METACLASS, data=linkData)

    def createLink(self, follower, targetNodes):
        """
        Create a link between a follower and other nodes.
        Default implementation just stores the given target nodes,
        and optionally calculates offsets.

        Args:
            follower (PyNode): The node to be linked such that it can be positioned later automatically
        """
        linkData = {
            'targetNodes': targetNodes,
        }

        if self.keepOffset:
            targetMtx = self.calculateTargetMatrix(follower, targetNodes, linkData)
            offsets = self.calculateOffsets(follower, targetMtx)
            linkData.update(offsets)

        self.setLinkMetaData(follower, linkData)

    def recreateLink(self, node, linkData):
        """
        Re-create the link between a follower and other nodes.
        Useful for updating offsets.
        """
        self.createLink(node, self.getTargetNodes(linkData))

    def calculateOffsets(self, follower, targetMtx):
        """
        Calculate the offset translate, rotate, and scale for a follower and target matrix.
        """
        precision = 5
        offsets = {}

        # get local matrix of follower relative to leader
        # for some reason TransformationMatrix is not invertible
        offsetMtx = pm.dt.TransformationMatrix(follower.wm.get() * pm.dt.Matrix(targetMtx).inverse())

        # translate
        offsets['offsetTranslate'] = [round(v, precision) for v in offsetMtx.getTranslation('world')]

        # rotate
        rot = offsetMtx.getRotation()
        rot.setDisplayUnit('degrees')
        offsets['offsetRotate'] = [round(v, precision) for v in rot]

        # scale
        offsets['offsetScale'] = [round(v, precision) for v in offsetMtx.getScale('world')]

        return offsets

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

    def applyLinkPosition(self, follower, linkData):
        """
        Update the transform of follower using it's link data
        """
        targetNodes = self.getTargetNodes(linkData)
        targetMtx = self.calculateTargetMatrix(follower, targetNodes, linkData)
        self.setFollowerMatrixWithOffset(follower, targetMtx, linkData)

    def calculateTargetMatrix(self, follower, targetNodes, linkData):
        """
        Calculate the target matrix to use for applying a linked position to the follower node.
        """
        return nodes.get_world_matrix(targetNodes[0])

    def setFollowerMatrixWithOffset(self, follower, targetMtx, linkData):
        """
        Set the new world matrix of a follower node, incorporating
        the saved offsets from linkData if applicable.
        """
        offsetMtx = self.getOffsetMatrix(linkData)
        newMtx = offsetMtx * targetMtx
        nodes.set_world_matrix(follower, newMtx)

    def getTargetNode(self, linkData):
        """
        Return the first target node of the link.
        """
        targetNodes = self.getTargetNodes(linkData)
        if targetNodes:
            return targetNodes[0]

    def getTargetNodes(self, linkData):
        return linkData.get('targetNodes', [])


class DefaultLinkPositioner(LinkPositioner):
    """
    Default link positioner, updates the follower to match a single leaders position.
    """

    linkType = LinkType.DEFAULT

    def calculateTargetMatrix(self, follower, targetNodes, linkData):
        """
        Calculate the target matrix to use for a linked node.
        """
        return nodes.get_world_matrix(targetNodes[0])


POSITIONER_CLASS_MAP[DefaultLinkPositioner.linkType] = DefaultLinkPositioner


class IKPoleLinkPositioner(LinkPositioner):
    """
    IK Pole positioner, updates the follower to be placed
    along the pole vector.
    """

    linkType = LinkType.IKPOLE

    def __init__(self):
        super().__init__()

        self.ikpoleDistance = None

    def createLink(self, follower, targetNodes):
        linkData = {
            'targetNodes': targetNodes,
        }

        if self.ikpoleDistance is not None:
            linkData['ikpoleDistance'] = self.ikpoleDistance

        self.setLinkMetaData(follower, linkData)

    def calculateTargetMatrix(self, follower, targetNodes, linkData):
        leader = targetNodes[0]
        poleVector, midPoint = joints.getIKPoleVectorAndMidPointForJoint(leader)

        distance = linkData.get('ikpoleDistance')
        if not distance:
            # calculate distance based on followers current location
            midToFollowerVector = follower.getTranslation(space='world') - midPoint
            distance = poleVector.dot(midToFollowerVector)

        newTranslate = midPoint + poleVector * distance
        targetMtx = pm.dt.TransformationMatrix(follower.wm.get())
        targetMtx.setTranslation(newTranslate, space='world')
        return targetMtx


POSITIONER_CLASS_MAP[IKPoleLinkPositioner.linkType] = IKPoleLinkPositioner


class WeightedLinkPositioner(LinkPositioner):
    """
    Weighted positioner updates the follower to be placed at a
    weighted location between targets.
    """

    linkType = LinkType.WEIGHTED

    def __init__(self):
        super().__init__()
        # the weights to use when creating a new link
        self.weights = None

    def createLink(self, follower, targetNodes):
        if self.weights is None:
            self.weights = [1] * len(targetNodes)
        elif len(targetNodes) != len(self.weights):
            raise ValueError('weights must be the same length as targetNodes')

        linkData = {
            'targetNodes': targetNodes,
            'weights': self.weights,
        }

        if self.keepOffset:
            targetMtx = self.calculateTargetMatrix(follower, targetNodes, linkData)
            offsets = self.calculateOffsets(follower, targetMtx)
            linkData.update(offsets)

        self.setLinkMetaData(follower, linkData)

    def recreateLink(self, node, linkData):
        self.weights = linkData.get('weights')
        self.createLink(node, self.getTargetNodes(linkData))

    def calculateTargetMatrix(self, follower, targetNodes, linkData):
        mtxs = [n.wm.get() for n in targetNodes]
        weights = linkData.get('weights', [])
        totalWeight = sum(weights)

        # pair and sort by weights, so the highest weight gets starting priority
        mtxWeights = list(zip(mtxs, weights))
        sorted(mtxWeights, key=operator.itemgetter(1), reverse=True)

        targetTranslate = pm.dt.TransformationMatrix(mtxs[0]).getTranslation(space='world')
        # blend to each following mtx using weights
        for mtx, weight in mtxWeights[1:]:
            alpha = weight / totalWeight
            translate = pm.dt.TransformationMatrix(mtx).getTranslation(space='world')
            targetTranslate = math.lerpVector(targetTranslate, translate, alpha)

        # currently only blending translate, the rest stays unmodified
        targetMtx = pm.dt.TransformationMatrix(follower.wm.get())
        targetMtx.setTranslation(targetTranslate, space='world')
        return targetMtx


POSITIONER_CLASS_MAP[WeightedLinkPositioner.linkType] = WeightedLinkPositioner
