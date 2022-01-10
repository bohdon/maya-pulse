import logging
import re

import pymel.core as pm

import pymetanode as meta
from . import colors
from . import joints
from . import links
from . import nodes
from .vendor.mayacoretools import preservedSelection

LOG = logging.getLogger(__name__)

MIRROR_METACLASS = 'pulse_mirror'
MIRROR_THRESHOLD = 0.0001


class MirrorMode(object):
    """
    Contains constants representing the available types of mirroring

    Simple:
        a ctl is mirrored across a single axis in the tranditional
        sense, this means the non-mirror axis basis vectors are flipped

    Aligned:
        a ctl is mirrored across a single axis in a visual sense,
        but the relationship between the matrices is more complicated.
        The result is an orientation that looks the same on both
        sides of an axis, as if they matched in world space in rest pose
    """

    Simple = 'simple'
    Aligned = 'aligned'


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
        LOG.debug("{0} paired node not found, "
                  "removing mirroring data".format(node))
        meta.removeMetaData(node, MIRROR_METACLASS)
        return False
    else:
        othersOther = getPairedNode(otherNode, False)
        if othersOther != node:
            LOG.debug("{0} pairing is unreciprocated, "
                      "removing mirror data".format(node))
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
        otherNode = getPairedNode(node)
        removeMirroringData(node)
        if otherNode:
            removeMirroringData(otherNode)


def duplicateAndPairNode(sourceNode):
    """
    Duplicate a node, and pair it with the node that was duplicated.

    Returns:
        The newly created node.
    """
    with preservedSelection():
        destNode = pm.duplicate(
            [sourceNode] + sourceNode.getChildren(s=True), po=True)[0]
        # handle bug in recent maya versions where extra empty
        # transforms will be included in the duplicate
        extra = destNode.listRelatives(typ='transform')
        if extra:
            LOG.debug("Deleting extra transforms from "
                      "mirroring: {0}".format(sourceNode))
            pm.delete(extra)
        # associate nodes
        pairMirrorNodes(sourceNode, destNode)
        return destNode


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


def getPairedNode(node, validate=True):
    """
    For a node with mirroring data, return the other node.

    Args:
        node: A node with mirroring data that references another node
        validate (bool): When true, ensures that the pairing is
            reciprocated by the other node
    """
    if isMirrorNode(node):
        data = meta.getMetaData(node, MIRROR_METACLASS)
        if validate:
            otherNode = data['otherNode']
            if otherNode and validate:
                if getPairedNode(otherNode, False) == node:
                    return otherNode
                else:
                    LOG.debug('{0} pairing not reciprocated'.format(node))
        else:
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
    absAxisVal = abs(node.getTranslation(space='world')[axis.index])
    return absAxisVal < MIRROR_THRESHOLD


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


def getBestMirrorMode(nodeA, nodeB):
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
        return MirrorMode.Aligned
    return MirrorMode.Simple


class MirrorOperation(object):
    """
    An operation that can be performed when mirroring nodes.
    Receives a call to mirror a sourceNode and targetNode.
    """

    def __init__(self):
        # the axis to mirror across
        self.axis = 0
        # if set, the custom matrix to use as the base for mirroring
        self.axisMatrix = None

    def mirrorNode(self, sourceNode, destNode, isNewNode):
        """
        Implement in subclasses to perform the mirroring operation.
        """
        raise NotImplementedError


class MirrorParenting(MirrorOperation):
    """
    Mirrors the parenting structure of nodes.
    """

    def __init__(self):
        super(MirrorParenting, self).__init__()
        # when true, will search for centered nodes for joints
        self.findCenteredJoints = True

    def mirrorNode(self, sourceNode, destNode, isNewNode):
        """
        Change the parent of destNode to match that of sourceNode,
        ensuring the use of paired nodes where possible to preserve
        a mirrored parenting structure.

        Handles joint parenting specially by checking for centered
        parents along an axis, as well as connecting inverse scales
        so that segment scale compensate still works.
        """
        with preservedSelection():
            # get parent of source node
            if self.findCenteredJoints and isinstance(sourceNode, pm.nt.Joint):
                srcParent = getMirroredOrCenteredParent(sourceNode, self.axis)
            else:
                srcParent = sourceNode.getParent()

            if srcParent:
                dstParent = getPairedNode(srcParent)
                if dstParent:
                    self.setParent(destNode, dstParent)
                else:
                    self.setParent(destNode, srcParent)
            else:
                self.setParent(destNode, None)

            # handle joint reparenting
            if isinstance(destNode, pm.nt.Joint):
                p = destNode.getParent()
                if p and isinstance(p, pm.nt.Joint):
                    if not pm.isConnected(p.scale, destNode.inverseScale):
                        p.scale >> destNode.inverseScale

    def setParent(self, node, parent):
        """
        Set the parent of a node. PyMel advertises that PyNode.setParent will not error
        if the parent is already the current parent, but it does error (tested Maya 2018).
        """
        if node.getParent() != parent:
            node.setParent(parent)


class MirrorTransforms(MirrorOperation):
    """
    Mirrors the transform matrices of nodes.
    Also provides additional functionality for 'flipping' node
    matrices (simultaneous mirroring on both sides).
    """

    def __init__(self):
        super(MirrorTransforms, self).__init__()

        # the type of transformation mirroring to use
        self.mirrorMode = MirrorMode.Simple

        self.useNodeSettings = True
        self.excludedNodeSettings = None
        self.mirroredAttrs = []
        self.customMirrorAttrExps = {}

        # used when getting mirrored matrices
        self.mirrorTranslate = True
        self.mirrorRotate = True
        self.mirrorRotateOrder = True

        # used when applying mirrored matrices
        self.setTranslate = True
        self.setRotate = True
        self.setScale = True
        self.setAttrs = True

    def _kwargsForGet(self):
        """
        Return kwargs for getMirrorSettings calls
        """
        keys = [
            'axis', 'axisMatrix', 'mirrorMode',
            'useNodeSettings', 'excludedNodeSettings',
            'mirroredAttrs', 'customMirrorAttrExps',
        ]
        kwargs = dict([(k, getattr(self, k)) for k in keys])
        kwargs['translate'] = self.mirrorTranslate
        kwargs['rotate'] = self.mirrorRotate
        return kwargs

    def _kwargsForApply(self):
        """
        Return kwargs for applyMirrorSettings calls
        """
        return dict(
            translate=self.setTranslate,
            rotate=self.setRotate,
            scale=self.setScale,
            attrs=self.setAttrs,
        )

    def mirrorNode(self, sourceNode, destNode, isNewNode):
        """
        Move a node to the mirrored position of another node.

        Args:
            sourceNode (PyNode): The node whos position will be used
            destNode (PyNode): The node to modify
            isNewNode (bool): Is the destination node newly created?
        """
        if self.mirrorRotateOrder:
            destNode.rotateOrder.set(sourceNode.rotateOrder.get())

        settings = getMirrorSettings(
            sourceNode, destNode, **self._kwargsForGet())
        if settings:
            applyMirrorSettings(settings, **self._kwargsForApply())

    def _prepareFlip(self, sourceNode, destNode):
        """
        Return settings gathered in preparation for flipping two nodes.
        """
        sourceSettings = getMirrorSettings(
            sourceNode, destNode, **self._kwargsForGet())
        destSettings = getMirrorSettings(
            destNode, sourceNode, **self._kwargsForGet())
        return (sourceSettings, destSettings)

    def _applyFlip(self, flipData):
        """
        Apply the flip data gathered from `_prepareFlip,` which will
        move the nodes to their flipped locations.
        """
        sourceSettings, destSettings = flipData
        if sourceSettings and destSettings:
            applyMirrorSettings(sourceSettings, **self._kwargsForApply())
            applyMirrorSettings(destSettings, **self._kwargsForApply())

    def flip(self, sourceNode, destNode):
        """
        Flip the transforms of two nodes such that each
        node moves to the mirrored transform of the other.
        """
        flipData = self._prepareFlip(sourceNode, destNode)
        self._applyFlip(flipData)

    def flipMultiple(self, nodePairs):
        """
        Perform `flip` on multiple nodes, by gathering first
        and then applying second, in order to avoid parenting
        and dependency issues.

        Args:
            nodePairs (list): A list of 2-tuple PyNodes representing
                (source, dest) node for each pair.
        """

        flipDataList = []
        for (source, dest) in nodePairs:
            flipData = self._prepareFlip(source, dest)
            flipDataList.append(flipData)

        for flipData in flipDataList:
            self._applyFlip(flipData)

    def flipCenter(self, nodes):
        """
        Move one or more non-mirrored nodes to the mirrored position
        of its current transform. The node list should be in order of
        dependency, where parents are first, followed by children in
        hierarchial order.
        """
        settings = []

        for n in nodes:
            kwargs = self._kwargsForGet()
            kwargs['mirrorMode'] = MirrorMode.Aligned
            kwargs['excludedNodeSettings'] = ['mirrorMode']
            s = getMirrorSettings(n, n, **kwargs)
            settings.append(s)

        # TODO: attempt to automatically handle parent/child relationships
        #       to lift the requirement of giving nodes in hierarchical order
        for s in settings:
            applyMirrorSettings(s, **self._kwargsForApply())


class MirrorCurveShapes(MirrorOperation):
    """
    Mirrors the NurbsCurve shapes of a node by simply
    flipping them, assuming MirrorTransformations would also
    be run on the mirrored nodes.
    """

    def __init__(self):
        super(MirrorCurveShapes, self).__init__()

        self.mirrorMode = MirrorMode.Simple

        # delete and replace curve shapes when mirroring
        self.replaceExistingShapes = True

        # the shape types to consider when replacing existing shapes
        self.shapeTypes = ['nurbsCurve']

    def mirrorNode(self, sourceNode, destNode, isNewNode):
        # curve shape mirroring doesn't care about the actual
        # position, its only job is to flip the curve
        if isNewNode:
            MirrorCurveShapes.flipAllCurveShapes(destNode, self.axis, self.mirrorMode)
        elif self.replaceExistingShapes:
            self.replaceCurveShapes(sourceNode, destNode)
            MirrorCurveShapes.flipAllCurveShapes(destNode, self.axis, self.mirrorMode)

    @staticmethod
    def flipAllCurveShapes(node, axis=0, mirrorMode=MirrorMode.Simple):
        """
        Flip the position of all cvs in all curve shapes of a node
        in a manner that corresponds to the transformation mirror modes.

        Args:
            curveShape (NurbsCurve):    The curve to mirror
            axis (int): An axis to mirror across
            mirrorMode: The MirrorMode type to use
        """
        shapes = node.getChildren(s=True)
        for shape in shapes:
            if hasattr(shape, "cv"):
                MirrorCurveShapes.flipCurveShape(shape, axis, mirrorMode)

    @staticmethod
    def flipCurveShape(curveShape, axis=0, mirrorMode=MirrorMode.Simple):
        """
        Flip the position of all cvs in a curve shape in a manner that
        corresponds to the transformation mirror modes.

        Args:
            curveShape (NurbsCurve):    The curve to mirror
            axis (int): An axis to mirror across
            mirrorMode: The MirrorMode type to use
        """
        if mirrorMode == MirrorMode.Simple:
            pm.scale(curveShape.cv, [-1, -1, -1])
        elif mirrorMode == MirrorMode.Aligned:
            s = [1, 1, 1]
            s[axis] = -1
            pm.scale(curveShape.cv, s)

    def replaceCurveShapes(self, sourceNode, destNode):
        """
        Copy the curve shapes from one node to another, clearing out any curve shapes
        in the destination node first.

        Args:
            sourceNode (pm.PyNode): The source node to copy shapes from
            destNode (pm.PyNode): The destination node to copy shapes to
        """
        dstShapes = destNode.getShapes(type=self.shapeTypes)
        if dstShapes:
            pm.delete(dstShapes)

        srcShapes = sourceNode.getShapes(type=self.shapeTypes)
        for shape in srcShapes:
            dupe = pm.duplicate(shape, addShape=True)
            pm.parent(dupe, destNode, shape=True, relative=True)


class MirrorJointDisplay(MirrorOperation):
    """
    Mirrors the display settings of joints
    """

    def mirrorNode(self, sourceNode, destNode, isNewNode):
        if sourceNode.type() == 'joint' and destNode.type() == 'joint':
            destNode.radius.set(sourceNode.radius.get())


class BlueprintMirrorOperation(MirrorOperation):
    """
    A MirrorOperation that makes use of a Blueprint config
    """

    def __init__(self):
        super(BlueprintMirrorOperation, self).__init__()
        # the Blueprint owner of the mirror operation
        self.blueprint = None
        # the Blueprint's config data
        self._config = None

    def getConfig(self):
        """
        Return the Blueprint's config. Caches the config
        on the first request.
        """
        if self._config is None:
            if self.blueprint:
                self._config = self.blueprint.getConfig()
            # if still no config, set to empty dict to prevent repeat check
            if self._config is None:
                self._config = {}
        return self._config


def _createNameReplacement(search, replace):
    """
    Return a tuple containing a regex and replacement string.
    Regexes replace prefixes, suffixes, or middles, as long as
    the search is separated with '_' from adjacent characters.
    """
    regex = re.compile('(?<![^_]){0}(?=(_|$))'.format(search))
    return (regex, replace)


def _generateMirrorNameReplacements(config):
    """
    Generate and return the full list of replacement pairs.

    Returns:
        A list of (regex, replacement) tuples.
    """
    replacements = []
    symConfig = config.get('symmetry', {})
    pairs = symConfig.get('pairs', [])

    for pair in pairs:
        if 'left' in pair and 'right' in pair:
            left = pair['left']
            right = pair['right']
            l2r = _createNameReplacement(left, right)
            r2l = _createNameReplacement(right, left)
            replacements.append(l2r)
            replacements.append(r2l)
        else:
            LOG.warning("Invalid symmetry pairs")

    return replacements


def _getMirroredNameWithReplacements(name, replacements):
    mirroredName = name
    for regex, repl in replacements:
        if regex.search(mirroredName):
            mirroredName = regex.sub(repl, mirroredName)
            break
    return mirroredName


def getMirroredName(name, config):
    """
    Given a string name, return the mirrored version considering
    all symmetry names defined in the Blueprint config.
    """
    replacements = _generateMirrorNameReplacements(config)
    return _getMirroredNameWithReplacements(name, replacements)


class MirrorNames(BlueprintMirrorOperation):
    """
    Mirrors the names of nodes.
    """

    def __init__(self):
        super(MirrorNames, self).__init__()
        # cached set of (regex, replacement) pairs
        self._replacements = None

    def getReplacements(self):
        """
        Return the list of regex and replacement pairs.
        Caches the list the first time it is requested so that
        subsequent calls are faster.
        """
        if self._replacements is None:
            self._replacements = _generateMirrorNameReplacements(
                self.getConfig())
        return self._replacements

    def mirrorNode(self, sourceNode, destNode, isNewNode):
        name = sourceNode.nodeName()
        destName = _getMirroredNameWithReplacements(
            name, self.getReplacements())
        destNode.rename(destName)


class MirrorColors(BlueprintMirrorOperation):
    """
    Mirrors the override display color of nodes.
    """

    def __init__(self):
        super(MirrorColors, self).__init__()
        # cached set of (regex, replacement) pairs
        self._replacements = None

    def getReplacements(self):
        """
        Return the list of regex and replacement pairs.
        Caches the list the first time it is requested so that
        subsequent calls are faster.
        """
        if self._replacements is None:
            self._replacements = _generateMirrorNameReplacements(
                self.getConfig())
        return self._replacements

    def mirrorNode(self, sourceNode, destNode, isNewNode):
        sourceColor = nodes.getOverrideColor(sourceNode)
        if sourceColor:
            sourceName = self.getColorName(sourceColor)
            if sourceName:
                destName = _getMirroredNameWithReplacements(
                    sourceName, self.getReplacements())
                destColor = self.getNamedColor(destName)
                if destColor:
                    nodes.setOverrideColor(destNode, destColor)

    def getNamedColor(self, name):
        """
        Return a color from the Blueprint config by name

        Returns:
            color (tuple of float)
        """
        configColors = self.getConfig().get('colors', [])
        for configColor in configColors:
            if configColor.get('name') == name:
                hexColor = configColor.get('color')
                if hexColor:
                    return colors.hexToRGB01(hexColor)

    def getColorName(self, color):
        """
        Return the name of a color, if it has one.

        Args:
            color (tuple of float): The color to search for
        """
        hexColor = colors.RGB01ToHex(color)
        configColors = self.getConfig().get('colors', [])
        for configColor in configColors:
            if configColor.get('color') == hexColor:
                return configColor.get('name')

        LOG.warning('Color has no name: %s (%s)', color, hexColor)


class MirrorLinks(BlueprintMirrorOperation):
    """
    Mirrors Blueprint links. See links.py
    """

    def mirrorNode(self, sourceNode, destNode, isNewNode):
        # get link meta data
        sourceLinkData = links.getLinkMetaData(sourceNode)
        destLinkData = links.getLinkMetaData(destNode)

        if sourceLinkData:
            # if no destination link data already exists, create
            # a copy of the source link data, otherwise only affect the target node
            if not destLinkData:
                destLinkData = sourceLinkData

            # TODO: provide a layer of abstraction, mirroring shouldn't have to know the details

            sourceTargetNodes = sourceLinkData.get('targetNodes')
            if sourceTargetNodes:
                destTargetNodes = [getPairedNode(n) for n in sourceTargetNodes]
                if destTargetNodes:
                    destLinkData['targetNodes'] = destTargetNodes
                    links.setLinkMetaData(destNode, destLinkData)

            # position the dest node using the link
            links.applyLinkPosition(destNode)

        elif destLinkData:
            # remove link data from dest node
            links.unlink(destNode)


class MirrorUtil(object):
    """
    A util class for performing MirrorOperations.
    Provides functionality for duplicating nodes that aren't paired,
    as well as performing the operations recursively on a node and
    all of its children.
    """

    def __init__(self):
        # the list of mirror operations to run, use add_operation
        self._operations = []

        # the axis to mirror across
        self.axis = 0
        # if set, the custom matrix to use as the base for mirroring
        self.axisMatrix = None

        # don't mirrored nodes that are centered along the mirror axis
        self.skipCentered = True

        # valid all source nodes before mirroring, potentially
        # cleaning or modifying their pairing data
        self.validateNodes = True

        # if True, allows nodes to be created if no pair exists
        self.isCreationAllowed = True

        # if True, applies operations to the nodes and all their children
        self.isRecursive = False

        # list of any nodes created during the operation, only valid
        # after creating node pairs, but before run() has finished
        self._newNodes = []

    def addOperation(self, operation):
        self._operations.append(operation)

    def run(self, sourceNodes):
        """
        Run all mirror operations on the given source nodes.
        """
        filteredNodes = self.gatherNodes(sourceNodes)
        pairs = self.createNodePairs(filteredNodes)
        for operation in self._operations:
            # ensure consistent mirroring settings for all operations
            self.configureOperation(operation)
            for pair in pairs:
                isNewNode = pair[1] in self._newNodes
                operation.mirrorNode(pair[0], pair[1], isNewNode)
        self._newNodes = []

    def shouldMirrorNode(self, sourceNode) -> bool:
        """
        Return whether the node sould be mirrored, or skipped.

        Accounts for special situations like centered joints,
        which may be included with recursive operations, but not
        wanted when mirroring.
        """
        if self.skipCentered:
            if isCentered(sourceNode, self.axis):
                return False

        return True

    def configureOperation(self, operation):
        """
        Configure a MirrorOperation instance.
        """
        operation.axis = self.axis
        operation.axisMatrix = self.axisMatrix

    def gatherNodes(self, sourceNodes):
        """
        Return a filtered and expanded list of sourceNodes to be mirrored,
        including children if isRecursive is True, and filtering nodes that
        should not be mirrored.
        """
        result = []

        if self.isRecursive:
            sourceNodes = nodes.getParentNodes(sourceNodes)

        # expand to children
        for sourceNode in sourceNodes:
            if sourceNode not in result:
                if self.shouldMirrorNode(sourceNode):
                    result.append(sourceNode)

            if self.isRecursive:
                children = nodes.getDescendantsTopToBottom(
                    sourceNode, type=['transform', 'joint'])

                for child in children:
                    if child not in result:
                        if self.shouldMirrorNode(child):
                            result.append(child)

        return result

    def createNodePairs(self, sourceNodes):
        """
        Iterate over a list of source nodes and retrieve or create
        destination nodes using pairing.
        """
        pairs = []

        for sourceNode in sourceNodes:
            if self.validateNodes:
                validateMirrorNode(sourceNode)

            if self.isCreationAllowed:
                destNode, isNewNode = self._getOrCreatePairNode(sourceNode)
                if destNode and isNewNode:
                    self._newNodes.append(destNode)
            else:
                destNode = getPairedNode(sourceNode)

            if destNode:
                pairs.append((sourceNode, destNode))
            else:
                LOG.warning("Could not get pair node for: "
                            "{0}".format(sourceNode))

        return pairs

    def _getOrCreatePairNode(self, sourceNode) -> pm.nt.Transform:
        """
        Return the pair node of a node, and if none exists,
        create a new pair node. Does not check isCreationAllowed.

        Returns:
            The pair node (PyNode), and a bool that is True if the
            node was just created, False otherwise.
        """
        destNode = getPairedNode(sourceNode)
        if destNode:
            return destNode, False
        else:
            destNode = duplicateAndPairNode(sourceNode)
            return destNode, True

    def getOrCreatePairNode(self, sourceNode) -> pm.nt.Transform:
        """
        Return the pair node of a node, and if none exists,
        create a new pair node. Does not check isCreationAllowed.
        """
        return self._getOrCreatePairNode(sourceNode)[0]


def getMirrorSettings(sourceNode, destNode=None,
                      useNodeSettings=True, excludedNodeSettings=None,
                      **kwargs):
    """
    Get mirror settings that represent mirroring from a source
    node to a target node.

    Args:
        sourceNode: A node to get matrix and other settings from
        destNode: A node that will have mirrored settings applied,
            necessary when evaluating custom mirroring attributes that
            need both nodes to compute
        useNodeSettings: A bool, whether to load custom settings from
            the node or not
        excludedNodeSettings: A list of settings to exclude when loading
            from node

    kwargs are divided up and used as necessary between 3 mirroring stages:
        See 'getMirroredMatrices' for a list of kwargs that can be given
        `mirroredAttrs` -- a list list of custom attribute names that will
            be included when mirroring
        `customMirrorAttrExps` -- a dictionary of {attr: expression} that
            are evaluated using the given sourceNode, destNode to determine
            custom mirroring behaviour for any attributes
    """

    def filterNodeSettings(settings):
        if excludedNodeSettings:
            return {k: v for k, v in settings.items()
                    if k not in excludedNodeSettings}
        return settings

    result = {}

    LOG.debug("Getting Mirror Settings: {0}".format(sourceNode))
    if not destNode:
        destNode = getPairedNode(sourceNode)
    if not destNode:
        return

    # if enabled, pull some custom mirroring settings from the node,
    # these are stored in a string attr as a python dict
    if useNodeSettings:
        data = meta.getMetaData(sourceNode, MIRROR_METACLASS)
        customSettings = data.get('customSettings')
        if customSettings is not None:
            LOG.debug("Custom Mirror Node")
            # nodeStngs = data['customSettings']
            LOG.debug("Settings: {0}".format(customSettings))
            kwargs.update(filterNodeSettings(customSettings))

    # pull some kwargs used for getMirroredMatrices
    matrixKwargs = dict([(k, v) for k, v in kwargs.items() if k in (
        'axis', 'axisMatrix', 'translate', 'rotate', 'mirrorMode')])
    result['matrices'] = getMirroredMatrices(sourceNode, **matrixKwargs)

    # add list of mirrored attributes as designated by kwargs
    mirAttrKwargs = dict([(a, getattr(sourceNode, a).get())
                          for a in kwargs.get('mirroredAttrs', [])])
    result.setdefault('mirroredAttrs', {}).update(mirAttrKwargs)

    for attr, exp in kwargs.get('customMirrorAttrExps', {}).items():
        if exp:
            LOG.debug("Attr: {0}".format(attr))
            LOG.debug("Exp:\n{0}".format(exp))
            val = evalCustomMirrorAttrExp(
                sourceNode, destNode, attr, exp)
            LOG.debug("Result: {0}".format(val))
            # Eval from the mirror to the dest
            result['mirroredAttrs'][attr] = val

    LOG.debug("Mirrored Attrs: {0}".format(result['mirroredAttrs']))

    # Save additional variables
    result['sourceNode'] = sourceNode
    result['destNode'] = destNode

    return result


def applyMirrorSettings(mirrorSettings,
                        translate=True, rotate=True, scale=True,
                        attrs=True):
    """
    Apply mirror settings created from getMirrorSettings
    """
    LOG.debug("Applying Mirror Settings: {0}".format(
        mirrorSettings['destNode']))
    settings = mirrorSettings
    if any([translate, rotate, scale]):
        setMirroredMatrices(settings['destNode'], settings['matrices'],
                            translate=translate, rotate=rotate, scale=scale)

    if attrs:
        LOG.debug("Applying Mirrored Attrs")
        for attrName, val in mirrorSettings.get('mirroredAttrs', {}).items():
            LOG.debug("{0} -> {1}".format(attrName, val))
            attr = settings['destNode'].attr(attrName)
            attr.set(val)


CUSTOM_EXP_FMT = """\
def exp():
    {body}return {lastLine}
result = exp()
"""


def evalCustomMirrorAttrExp(sourceNode, destNode, attr, exp):
    result = {}

    LOG.debug("Raw Exp: {0}".format(repr(exp)))
    _globals = {}
    _globals['node'] = sourceNode
    _globals['dest_node'] = destNode
    if hasattr(sourceNode, attr):
        _globals['value'] = getattr(sourceNode, attr).get()
    else:
        raise KeyError(
            "{0} missing mirrored attr {1}".format(sourceNode, attr))
    if hasattr(destNode, attr):
        _globals['dest_value'] = getattr(destNode, attr).get()
    else:
        raise KeyError("{0} missing mirrored attr {1}".format(destNode, attr))

    # Add a return to the last line of the expression
    # so we can treat it as a function
    body = [l for l in exp.strip().split('\n') if l]
    lastLine = body.pop(-1)
    _exp = CUSTOM_EXP_FMT.format(
        body='\n\t'.join(body + ['']), lastLine=lastLine)

    # TODO: do this without exec
    exec(_exp, _globals)
    result = _globals['result']

    return result


def getMirroredMatrices(node,
                        axis=0, axisMatrix=None,
                        translate=True, rotate=True,
                        mirrorMode=MirrorMode.Simple):
    """
    Return the mirrored matrix or matrices for the given node
    Automatically handles Transform vs. Joint differences

    Args:
        axis (int): An axis to mirror across
        axisMatrix: the matrix in which we should mirror
        translate (bool): If False, the matrix will not be moved
        rotate (bool): If False, the matrix will not be rotated
        mirrorMode: what type of mirroring should be performed, see `MirrorMode`
    """
    # build kwargs for both commands
    kwargs = dict(
        axis=axis,
        axisMatrix=axisMatrix,
        translate=translate,
        rotate=rotate,
        mirrorMode=mirrorMode,
    )
    result = {}
    if isinstance(node, pm.nt.Joint):
        result['type'] = 'joint'
        jmatrices = joints.getJointMatrices(node)
        result['matrices'] = getMirroredJointMatrices(*jmatrices, **kwargs)
    else:
        result['type'] = 'node'
        result['matrices'] = [getMirroredTransformMatrix(
            nodes.getWorldMatrix(node), **kwargs)]
    return result


def setMirroredMatrices(node, mirroredMatrices,
                        translate=True, rotate=True, scale=True):
    """
    Set the world matrix for the given node using the given mirrored matrices
    Automatically interprets Transform vs. Joint matrix settings
    """
    if mirroredMatrices['type'] == 'joint':
        LOG.debug("Applying Joint Matrices")
        joints.setJointMatrices(node, *mirroredMatrices['matrices'], translate=translate, rotate=rotate)
    else:
        LOG.debug("Applying Transform Matrix")
        nodes.setWorldMatrix(node, *mirroredMatrices['matrices'], translate=translate, rotate=rotate, scale=scale)


def getMirroredTransformMatrix(matrix,
                               axis=0, axisMatrix=None,
                               translate=True, rotate=True,
                               mirrorMode=MirrorMode.Simple):
    """
    Return the mirrored version of the given matrix.

    Args:
        axis (int): An axis to mirror across
        axisMatrix: A matrix in which we should mirror
        translate (bool): If False, the matrix will not be moved
        rotate (bool): If False, the matrix will not be rotated
        mirrorMode: what type of mirroring should be performed,
            default is MirrorMode.Simple
    """
    axis = nodes.getAxis(axis)
    if axisMatrix is not None:
        # remove scale from the axisMatrix
        axisMatrix = nodes.getScaleMatrix(
            axisMatrix).inverse() * axisMatrix
        matrix = matrix * axisMatrix.inverse()
    s = nodes.getScaleMatrix(matrix)
    r = nodes.getRotationMatrix(matrix)
    t = matrix[3]
    if translate:
        # negate translate vector
        t[axis.index] = -t[axis.index]
    if rotate:
        r = invertOtherAxes(r, axis)
        if mirrorMode == MirrorMode.Aligned:
            LOG.debug("Counter Rotating because mirror mode is Aligned")
            r = counterRotateForNonMirrored(r, axis)
    mirror = s * r
    mirror[3] = t
    if axisMatrix is not None:
        mirror = mirror * axisMatrix
    return mirror


def getMirroredJointMatrices(matrix, r, ra, jo,
                             axis=0, axisMatrix=None,
                             translate=True, rotate=True,
                             mirrorMode=MirrorMode.Simple):
    """
    Return the given joint matrices mirrored across the given axis.
    Returns the full transformation matrix, rotation, rotation axis,
    and joint orient matrices.

    Args:
        axis (int): An axis to mirror across
        axisMatrix: A matrix in which we should mirror
        translate (bool): If False, the matrix will not be moved
        rotate (bool): If False, the matrix will not be rotated
        mirrorMode: what type of mirroring should be performed,
            default is MirrorMode.Simple
    """
    LOG.debug("Getting Mirrored Joint Matrices")
    # matches transform orientation
    mirror = getMirroredTransformMatrix(
        matrix, axis, axisMatrix, translate, rotate)
    if rotate:
        if axisMatrix is not None:
            # matches orientation with jo
            invScaleMtx = nodes.getScaleMatrix(axisMatrix).inverse()
            axisMatrix = invScaleMtx * axisMatrix
            jo = jo * axisMatrix.inverse()
        # flips orientation
        jo = invertOtherAxes(jo, axis)
        if mirrorMode == MirrorMode.Aligned:
            LOG.debug("Counter Rotating because mirror mode is Aligned")
            # changes orientation to inverted world
            jo = counterRotateForMirroredJoint(jo)
        if axisMatrix is not None:
            # doesnt seem to do anything
            jo = jo * axisMatrix
    return mirror, r, ra, jo


def invertOtherAxes(matrix, axis=0):
    """
    Invert the other axes of the given rotation
    matrix based on rows of the matrix.
    """
    axis = nodes.getAxis(axis)
    others = nodes.getOtherAxes(axis)
    x, y, z = matrix[:3]
    for v in (x, y, z):
        for a in others:
            v[a.index] *= -1
    return pm.dt.Matrix(x, y, z)


def counterRotateForNonMirrored(matrix, axis=0):
    """
    Essentially rotates 180 on the given axis,
    this is used to create mirroring when ctls
    are setup to not be mirrored at rest pose.
    """
    axis = nodes.getAxis(axis)
    others = [o.index for o in nodes.getOtherAxes(axis)]
    x, y, z = matrix[:3]
    for i, row in enumerate((x, y, z)):
        if i in others:
            for col in range(3):
                row[col] *= -1
    return pm.dt.Matrix(x, y, z)


def counterRotateForMirroredJoint(matrix):
    """
    Essentially rotates 180 on the given axis,
    this is used to create mirroring when ctls
    are setup to not be mirrored at rest pose.
    """
    x, y, z = matrix[:3]
    for row in (x, y, z):
        for col in range(3):
            row[col] *= -1
    return pm.dt.Matrix(x, y, z)
