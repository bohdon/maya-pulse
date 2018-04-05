
import logging
import pymel.core as pm
import pymetanode as meta
from vendor.mayacoretools import preservedSelection

from . import nodes
from . import joints

__all__ = [
    'applyMirrorSettings',
    'counterRotateForMirroredJoint',
    'counterRotateForNonMirrored',
    'evalCustomMirrorAttrExp',
    'getAllMirrorNodes',
    'getBestMirrorMode',
    'getCenteredParent',
    'getMirroredJointMatrices',
    'getMirroredMatrices',
    'getMirroredOrCenteredParent',
    'getMirroredParent',
    'getMirroredTransformMatrix',
    'getMirrorSettings',
    'getPairedNode',
    'invertOtherAxes',
    'isCentered',
    'isMirrorNode',
    'MirrorUtil',
    'removeMirroringData',
    'setMirroredMatrices',
    'setMirroringData',
    'validateMirrorNode',
]

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
        otherNode = getPairedNode(node)
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


def getPairedNode(node):
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


class MirrorUtil(object):
    """
    A util class that can duplicate nodes,
    apply mirrored transform matrices, as well
    as modify parenting and node hierarchies to
    achieve symmetry.

    The primary methods are:
        createMirror() -- handles duplicating nodes and
            associating them as mirrors, deals with joints
        mirrorTransform() -- handles the actual mirroring
            and application of matrices between mirror nodes
        mirrorParenting() -- reparents nodes based on their
            mirror nodes parent, handles joints specially

    These three operations can be performed together using
    the 'mirror()' method. There are also recursive methods
    available for each of these.

    """

    # TODO: make individual mirroring util classes for each operation

    def __init__(self):
        # the axis to mirror across
        self.axis = 0
        # if set, the custom matrix to use as the base for mirroring
        self.axisMatrix = None
        # the type of transformation mirroring to use
        self.mirrorMode = MirrorMode.Simple

        # if True, replace existing nodes during create operation
        self.replace = False

        # if True, joints are treated specially such that centered
        # joints remain unpaired
        self.handleJoints = True

        self.useNodeSettings = True
        self.excludedNodeSettings = None
        self.mirroredAttrs = []
        self.customMirrorAttrExps = {}

        # used when getting mirrored matrices
        self.mirrorTranslate = True
        self.mirrorRotate = True

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

    def _recursive(self, fnc, node, depthLimit=-1):
        """
        Run the function with the given node and all
        its relatives.
        """
        def recurseFnc(node, depth):
            result = [fnc(node)]
            if depthLimit < 0 or depth < depthLimit:
                for child in node.getChildren(typ='transform'):
                    result.extend(recurseFnc(child, depth + 1))
            return result
        return recurseFnc(node, 0)

    def mirror(self, sourceNodes, create=True, reparent=True, transform=True):
        """
        Run multiple mirroring operations at once.

        Args:
            sourceNodes: A list of nodes
            create: A bool, when True, runs createMirror
            reparent: A bool, when True, runs mirrorParenting
            transform: A bool, when True, runs mirrorTransform

        Returns the mirrored nodes (if create is True), otherwise None
        """
        destNodes = []
        if create:
            for n in sourceNodes:
                destNodes.append(self.createMirror(n))
        if reparent:
            for n in sourceNodes:
                self.mirrorParenting(n)
        if transform:
            for n in sourceNodes:
                self.mirrorTransform(n)
        return destNodes

    def mirrorRecursive(self, sourceNodes, create=True, reparent=True, transform=True):
        """
        Run multiple mirroring operations at once, recursively

        Args:
            sourceNodes: A list of nodes
            create: A bool, when True, runs createMirror
            reparent: A bool, when True, runs mirrorParenting
            transform: A bool, when True, runs mirrorTransform

        Returns the mirrored nodes (if create is True), otherwise None
        """
        destNodes = []
        if create:
            for n in sourceNodes:
                destNodes.extend(self.createMirrorRecursive(n))
        if reparent:
            for n in sourceNodes:
                self.mirrorParentingRecursive(n)
        if transform:
            for n in sourceNodes:
                self.mirrorTransformRecursive(n)
        return destNodes

    def createMirror(self, sourceNode):
        """
        Duplicate a node and pair it for mirroring.
        Does not actually mirror the transform matrix of the new node,
        simply creates an exact duplicate in place.
        """
        with preservedSelection():
            destNode = None
            if not self.replace:
                # look for existing mirror node
                destNode = getPairedNode(sourceNode)
            if not destNode:

                if self.handleJoints and isinstance(sourceNode, pm.nt.Joint):
                    if isCentered(sourceNode, self.axis):
                        # skip centered joints
                        # TODO: make sure returning None is fine
                        return

                destNode = pm.duplicate(
                    [sourceNode] + sourceNode.getChildren(s=True), po=True)[0]
                # handle bug in recent maya versions where extra empty transforms
                # will be included in the duplicate
                extra = destNode.listRelatives(typ='transform')
                if extra:
                    LOG.debug('Deleting extra transforms from mirroring: {0}'.format(sourceNode))
                    pm.delete(extra)
                # associate nodes
                pairMirrorNodes(sourceNode, destNode)
            return destNode

    def mirrorParenting(self, sourceNode, destNode=None):
        """
        Reparent the paired node of sourceNode to form a symmetrical hierarchy.
        If sourceNode's parent is not a mirrored node, reparent the node so that
        the two nodes share the same parent.

        Optionally, handle joint parenting specially, eg. connecting
        inverse scales so that segment scale compensate still works
        """
        with preservedSelection():
            if not destNode:
                destNode = getPairedNode(sourceNode)
            if not destNode:
                return

            # get parent of source node
            if self.handleJoints and isinstance(sourceNode, pm.nt.Joint):
                srcParent = getMirroredOrCenteredParent(sourceNode, self.axis)
            else:
                srcParent = sourceNode.getParent()

            if srcParent:
                dstParent = getPairedNode(srcParent)
                if dstParent:
                    destNode.setParent(dstParent)
                else:
                    destNode.setParent(srcParent)
            else:
                destNode.setParent(None)

            # handle joint reparenting
            if isinstance(destNode, pm.nt.Joint):
                p = destNode.getParent()
                if p and isinstance(p, pm.nt.Joint):
                    if not pm.isConnected(p.scale, destNode.inverseScale):
                        p.scale >> destNode.inverseScale

    def mirrorTransform(self, sourceNode, destNode=None):
        """
        Move the paired node of sourceNode to the mirrored transform of sourceNode.
        """
        settings = getMirrorSettings(sourceNode, destNode, **self._kwargsForGet())
        if settings:
            applyMirrorSettings(settings, **self._kwargsForApply())

    def createMirrorRecursive(self, sourceNode, depthLimit=-1):
        """
        Perform `createMirror` recursively on a node and all its children.

        `depthLimit` -- how many levels to recurse, default is -1 (infinite)
        """
        return self._recursive(self.createMirror, sourceNode, depthLimit)

    def mirrorParentingRecursive(self, sourceNode, depthLimit=-1):
        """
        Perform `mirrorParenting` recursively on a node and all its children.

        `depthLimit` -- how many levels to recurse, default is -1 (infinite)
        """
        return self._recursive(self.mirrorParenting, sourceNode, depthLimit)

    def mirrorTransformRecursive(self, sourceNode, depthLimit=-1):
        """
        Perform `mirrorTransform` recursively on a node and all its children.

        `depthLimit` -- how many levels to recurse, default is -1 (infinite)
        """
        return self._recursive(self.mirrorTransform, sourceNode, depthLimit)

    def flip(self, sourceNode, destNode=None):
        """
        Flip the transforms of two nodes such that each
        node moves to the mirrored transform of its counterpart.
        """
        if not destNode:
            destNode = getPairedNode(sourceNode)
            if not destNode:
                return

        sourceSettings = getMirrorSettings(
            sourceNode, destNode, **self._kwargsForGet())
        destSettings = getMirrorSettings(
            destNode, sourceNode, **self._kwargsForGet())
        if sourceSettings and destSettings:
            applyMirrorSettings(sourceSettings, **self._kwargsForApply())
            applyMirrorSettings(destSettings, **self._kwargsForApply())

    def flipMultiple(self, sourceNodes, destNodes=None):
        """
        Perform `flip` on multiple nodes, handling parenting
        and ordering of operations automatically.
        """
        if destNodes is None:
            destNodes = [None] * len(sourceNodes)
        # make sure lists are the same length
        if len(sourceNodes) != len(destNodes):
            LOG.error("sourceNodes list is not the same length as destNodes list")
            return
        # get any target nodes that are None automatically
        for i, source in enumerate(sourceNodes):
            if destNodes[i] is None:
                destNodes[i] = getPairedNode(source)

        allSettings = []

        for i, source in enumerate(sourceNodes):
            if destNodes[i] is not None:
                srcStngs = getMirrorSettings(
                    source, destNodes[i], **self._kwargsForGet())
                dstStngs = getMirrorSettings(
                    destNodes[i], source, **self._kwargsForGet())
                allSettings.append((srcStngs, dstStngs))

        for srcStngs, dstStngs in allSettings:
            applyMirrorSettings(srcStngs, **self._kwargsForApply())
            applyMirrorSettings(dstStngs, **self._kwargsForApply())

    def flipCenter(self, sourceNodes):
        """
        Given a list of non-mirrored nodes, move each node to the
        mirrored version of its current transform. The node list must be
        in order of dependency, where parents are first, followed
        by children in hierarchial order.
        """
        settings = []
        # get all at once
        for n in sourceNodes:
            kwargs = self._kwargsForGet()
            kwargs['mirrorMode'] = MirrorMode.Aligned
            kwargs['excludedNodeSettings'] = ['mirrorMode']
            s = getMirrorSettings(n, n, **kwargs)
            settings.append(s)
        # set all at once
        # assumes selection is in parent -> child order
        # TODO: recursively re-attempt application of mirror settings
        #       to prevent having to pass the nodes in the correct order
        for s in settings:
            applyMirrorSettings(s, **self._kwargsForApply())



def getMirrorSettings(sourceNode, destNode=None, useNodeSettings=True, excludedNodeSettings=None, **kwargs):
    """
    Get mirror settings that represent mirroring from a source node to a target node.

    Args:
        sourceNode: A node to get matrix and other settings from
        destNode: A node that will have mirrored settings applied, this is
            used when evaluating custom mirroring attributes that need both nodes to compute
        useNodeSettings: A bool, whether to load custom settings from the node or not
        excludedNodeSettings: A list of settings to exclude when loading from node

    kwargs are divided up and used as necessary between 3 mirroring stages:
        See 'getMirroredMatrices' for a list of kwargs that can be given
        `mirroredAttrs` -- a list list of custom attribute names that will be included when mirroring
        `customMirrorAttrExps` -- a dictionary of {attr: expression} that are evaluated
            using the given sourceNode, destNode to determine custom mirroring behaviour
            for any attributes
    """

    def filterNodeSettings(settings):
        if excludedNodeSettings:
            return {k:v for k,v in settings.iteritems() if k not in excludedNodeSettings}
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
        customSettings = data.get('customSettings', None)
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


def applyMirrorSettings(mirrorSettings, translate=True, rotate=True, scale=True, attrs=True):
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
        raise KeyError("{0} missing mirrored attr {1}".format(sourceNode, attr))
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


def getMirroredMatrices(node, axis=0, axisMatrix=None, translate=True, rotate=True, mirrorMode=MirrorMode.Simple):
    """
    Return the mirrored matrix or matrices for the given node
    Automatically handles Transform vs. Joint differences

    Args:
        axis: the axis about which to mirror
        axisMatrix: the matrix in which we should mirror
        translate: A bool, if False, the matrix will not be moved
        rotate: A bool, if False, the matrix will not be rotated
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


def setMirroredMatrices(node, mirroredMatrices, translate=True, rotate=True, scale=True):
    """
    Set the world matrix for the given node using the given mirrored matrices
    Automatically interprets Transform vs. Joint matrix settings
    """
    if mirroredMatrices['type'] == 'joint':
        LOG.debug("Applying Joint Matrices")
        joints.setJointMatrices(node, *mirroredMatrices['matrices'],
                                translate=translate,
                                rotate=rotate
                                )
    else:
        LOG.debug("Applying Transform Matrix")
        nodes.setWorldMatrix(node, *mirroredMatrices['matrices'],
                             translate=translate,
                             rotate=rotate,
                             scale=scale
                             )


def getMirroredTransformMatrix(matrix, axis=0, axisMatrix=None, translate=True, rotate=True, mirrorMode=MirrorMode.Simple):
    """
    Return the mirrored version of the given matrix.

    Args:
        axis: A axis about which to mirror
        axisMatrix: A matrix in which we should mirror
        translate: A bool, if False, the matrix will not be moved
        rotate: A bool, if False, the matrix will not be rotated
        mirrorMode: what type of mirroring should be performed, default is MirrorMode.Simple
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


def getMirroredJointMatrices(matrix, r, ra, jo, axis=0, axisMatrix=None, translate=True, rotate=True, mirrorMode=MirrorMode.Simple):
    """
    Return the given joint matrices mirrored across the given axis.
    Returns the full transformation matrix, rotation, rotation axis, and joint orient matrices.

    Args:
        axis: A axis about which to mirror
        axisMatrix: A matrix in which we should mirror
        translate: A bool, if False, the matrix will not be moved
        rotate: A bool, if False, the matrix will not be rotated
        mirrorMode: what type of mirroring should be performed, default is MirrorMode.Simple
    """
    LOG.debug("Getting Mirrored Joint Matrices")
    #matches transform orientation
    mirror = getMirroredTransformMatrix(
        matrix, axis, axisMatrix, translate, rotate)
    if rotate:
        if axisMatrix is not None:
            # matches orientation with jo
            axisMatrix = nodes.getScaleMatrix(axisMatrix).inverse() * axisMatrix
            jo = jo * axisMatrix.inverse()
        # flips orientation
        jo = invertOtherAxes(jo, axis)
        if mirrorMode == MirrorMode.Aligned:
            LOG.debug("Counter Rotating because mirror mode is Aligned")
            # changes orientation to inverted world
            jo = counterRotateForMirroredJoint(jo)
            #r = counterRotateForNonMirrored(jo, axis) -- wrong matrix fyi joints should have no rots.
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
