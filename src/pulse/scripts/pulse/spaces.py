"""
Space Switching Constraint Setup
    - Store offsets from each space node in new attrs on the follower
        (follower.wm * space.wm.inverse)
    - Connect all offset matrices to 'offsetChoice' (choice) node
    - Connect all space node world matrices to 'spaceChoice' (choice) node
    - Connect 'space' attribute (enum) to selector of both choice nodes
    - Connect output of choices to calc new follower world matrix (multMatrix)
        (offsetChoice.output * spaceChoice.output)
    - Connect output matrix to offsetParentMatrix of follower

Space Switching Constraint Setup (2019 and older)
    - Store offsets from each space node in new attrs on the follower
        (follower.wm * space.wm.inverse)
    - Connect all offset matrices to 'offsetChoice' (choice) node
    - Connect all space node world matrices to 'spaceChoice' (choice) node
    - Connect 'space' attribute (enum) to selector of both choice nodes
    - Connect output of choices to calc new follower world matrix (multMatrix)
        (offsetChoice.output * spaceChoice.output * follower.pim)
    - Decompose and connect to follower trs (will occupy transform attributes, so this
        requires the use of an offset transform for anim controls)

(see space switching solution by Jarred Love)

"""

import logging

import maya.cmds as cmds
import pymel.core as pm

import pymetanode as meta
from . import utilnodes

LOG = logging.getLogger(__name__)

SPACE_METACLASS = 'pulse_space'
SPACECONSTRAINT_METACLASS = 'pulse_space_con'
SPACESWITCH_ATTR = 'space'


def getAllSpaces():
    """
    Return a list of all space nodes
    """
    return meta.findMetaNodes(SPACE_METACLASS)


def getAllSpacesIndexedByName():
    """
    Return all space nodes in a dict indexed by their space name
    """
    allSpaceNodes = getAllSpaces()
    result = {}
    for spaceNode in allSpaceNodes:
        spaceData = meta.getMetaData(spaceNode, SPACE_METACLASS)
        result[spaceData['name']] = spaceNode
    return result


def isSpace(node):
    """
    Return True if the node is a space

    Args:
        node: A PyNode or string node name
    """
    return meta.hasMetaClass(node, SPACE_METACLASS)


def getAllSpaceConstraints():
    """
    Return a list of all space constrained nodes
    """
    return meta.findMetaNodes(SPACECONSTRAINT_METACLASS)


def isSpaceConstraint(node):
    """
    Return True if the node is space constrained

    Args:
        node: A PyNode or string node name
    """
    return meta.hasMetaClass(node, SPACECONSTRAINT_METACLASS)


def createSpace(node, name):
    """
    Create a new space

    Args:
        node: A PyNode or string node name
        name: A string name of the space to create
    """
    data = {
        'name': name,
    }
    meta.setMetaData(node, SPACE_METACLASS, data)


def setupSpaceConstraint(node, spaceNames, follower=None, useOffsetMatrix=True):
    """
    Set up a node to be constrained for a space switch, but do not
    actually connect it to the desired spaces until `connectSpaceConstraint` is called.
    This is necessary because the transforms that represent each space may not
    have been defined yet, but the desire to constrain to them by space name can be expressed
    ahead of time.

    Args:
        node (PyNode): The node that will contain space switching attrs
        spaceNames (str list): The names of all spaces to be applied
        follower (PyNode): If given, the node that will be constrained, otherwise
            `node` will be used. Useful when wanting to create the space constrain attributes
            on an animation control, but connect the actual constraint to a parent transform
        useOffsetMatrix (bool): When true, will connect to the offsetParentMatrix
            of the follower node, instead of directly into the translate, rotate, and scale.
            This also eliminates the necessity for a decompose matrix node.
    """
    if useOffsetMatrix and cmds.about(api=True) < 20200000:
        # not supported before Maya 2020
        useOffsetMatrix = False

    if not follower:
        follower = node

    # setup space switching attr
    if not node.hasAttr(SPACESWITCH_ATTR):
        enumNames = ':'.join(spaceNames)
        node.addAttr(SPACESWITCH_ATTR, at='enum', en=enumNames)
        spaceAttr = node.attr(SPACESWITCH_ATTR)
        spaceAttr.setKeyable(True)
    else:
        spaceAttr = node.attr(SPACESWITCH_ATTR)

    nodeName = node.nodeName()

    offsetChoiceName = nodeName + '_spaceOffset_choice'
    spaceChoiceName = nodeName + '_space_choice'
    multMatrixName = nodeName + '_space_mmtx'
    decompName = nodeName + '_space_decomp'

    # create utility nodes
    offsetChoice = pm.shadingNode('choice', n=offsetChoiceName, asUtility=True)
    spaceChoice = pm.shadingNode('choice', n=spaceChoiceName, asUtility=True)
    utilnodes.loadMatrixPlugin()
    multMatrix = pm.shadingNode('multMatrix', n=multMatrixName, asUtility=True)
    if not useOffsetMatrix:
        decomp = pm.shadingNode(
            'decomposeMatrix', n=decompName, asUtility=True)

    # setup connections
    spaceAttr >> offsetChoice.selector
    spaceAttr >> spaceChoice.selector
    offsetChoice.output >> multMatrix.matrixIn[0]
    spaceChoice.output >> multMatrix.matrixIn[1]
    # follower.pim >> multMatrix.matrixIn[2]
    if not useOffsetMatrix:
        multMatrix.matrixSum >> decomp.inputMatrix
    # final connection to the follower occurs
    # during connectSpaceConstraint.

    spaceData = []
    # native space indeces always take priority,
    # which means dynamic spaces may be adversely affected
    # if the native spaces change on a published rig
    # TODO: ability to reindex dynamic spaces
    for i, spaceName in enumerate(spaceNames):
        spaceData.append({
            'name': spaceName,
            # TODO: is `switch` needed anymore?
            'switch': None,
            'index': i,
        })

    data = {
        # native spaces in this constraint
        'spaces': spaceData,
        # dynamic spaces (added during animation), which may be
        # from the native rig, or from an external one
        'dynamicSpaces': [],
        # transform that is actually driven by the space constraint
        'follower': follower,
        # the utility nodes that make up the space constraint
        'offsetChoice': offsetChoice,
        'spaceChoice': spaceChoice,
        'multMatrix': multMatrix,
        'useOffsetMatrix': useOffsetMatrix,
    }
    if not useOffsetMatrix:
        # decomp only exists when not using offset matrix
        data['decompose'] = decomp

    meta.setMetaData(node, SPACECONSTRAINT_METACLASS, data)


def _setupSpaceConstraintAttrs(node, spaceNames):
    # setup space switching attr
    if not node.hasAttr(SPACESWITCH_ATTR):
        enumNames = ':'.join(spaceNames)
        node.addAttr(SPACESWITCH_ATTR, at='enum', en=enumNames)
        spaceAttr = node.attr(SPACESWITCH_ATTR)
        spaceAttr.setKeyable(True)
    else:
        spaceAttr = node.attr(SPACESWITCH_ATTR)


def connectSpaceConstraints(nodes):
    """
    Create the actual constraints for a list of prepared
    space constraints. This is more efficient than calling
    connectSpaceConstraint for each node since all
    spaces are gathered only once.
    """
    spaceNodesByName = getAllSpacesIndexedByName()

    allConstraints = getAllSpaceConstraints()
    for constraint in allConstraints:
        _connectSpaceConstraint(constraint, spaceNodesByName)


def connectSpaceConstraint(node):
    """
    Create the actual constraints for each defined space in
    a space constraint node.

    Args:
        node (PyNode): The space constraint node
    """
    if not isSpaceConstraint(node):
        # TODO: warn
        return

    spaceNodesByName = getAllSpacesIndexedByName()
    _connectSpaceConstraint(node, spaceNodesByName)


def _connectSpaceConstraint(node, spaceNodesByName):
    """
    Connect all spaces defined in the node's space data
    to the space constraint utility nodes.

    Args:
        node (PyNode): The space constraint node
        spaceNodesByName (dict): A dict of the space
            nodes index by name.
    """
    data = meta.getMetaData(node, SPACECONSTRAINT_METACLASS)
    didConnectAny = False
    for spaceData in data['spaces']:
        index = spaceData['index']
        # ensure the switch is not already created
        if not spaceData['switch']:
            spaceNode = spaceNodesByName.get(spaceData['name'], None)
            if spaceNode:
                _connectSpaceToConstraint(data, index, spaceNode)
                didConnectAny = True
            else:
                LOG.warning(
                    "Space node not found: {0}".format(spaceData['name']))

    if didConnectAny:
        # connect final output now that at least one space is connected
        # TODO: make sure the space 0 is setup, or whatever the attrs value is
        follower = data['follower']
        useOffsetMatrix = data['useOffsetMatrix']

        if useOffsetMatrix:
            multMatrix = data['multMatrix']
            multMatrix.matrixSum >> follower.offsetParentMatrix
        else:
            decomp = data['decompose']
            decomp.outputTranslate >> follower.translate
            decomp.outputRotate >> follower.rotate
            decomp.outputScale >> follower.scale

        # no longer need to inherit transform
        follower.inheritsTransform.set(False)


def _connectSpaceToConstraint(spaceConstraintData, index, spaceNode):
    """
    Connect a space node to a space constraint choice and calculate the
    preserved offset matrix for the space as well.

    Args:
        spaceConstraintData (dict): The loaded space constraint data
            from the space constraint node
        index (int): The index of the space being connected
        spaceNode (PyNode): The node representing the space
    """
    # connect space node world matrix to choice node
    spaceChoice = spaceConstraintData['spaceChoice']
    spaceNode.wm >> spaceChoice.input[index]

    # calculate the offset between the space and follower
    follower = spaceConstraintData['follower']
    useOffsetMatrix = spaceConstraintData['useOffsetMatrix']
    if useOffsetMatrix:
        # calculate an offset matrix that doesn't include the local matrix of the follower,
        # so that the result can be plugged into the offsetParentMatrix of the follower
        offsetMtx = follower.pm.get() * spaceNode.wim.get()
    else:
        # the space constraint will go directly into the transform
        # attrs of the follower, so it should include all of the follower world matrix
        offsetMtx = follower.wm.get() * spaceNode.wim.get()

    # store the offset matrix on the offset choice node
    offsetChoice = spaceConstraintData['offsetChoice']
    # create a matrix attribute on the choice node to hold the offset
    # (the choice input attributes are wildcards and cannot hold matrix data)
    offsetAttrName = 'offset{}'.format(index)
    offsetChoice.addAttr(offsetAttrName, dt='matrix')
    offsetAttr = offsetChoice.attr(offsetAttrName)
    offsetAttr.set(offsetMtx)
    offsetAttr >> offsetChoice.input[index]


def _getAllSpacesInConstraint(spaceConstraintData):
    """
    Return a combined list of native and dynamic spaces for a constraint.

    Args:
        spaceConstraintData (dict): The loaded space constraint data
            from the space constraint node

    Returns:
        A list of dict representing spaces applied to a constraint.
        See `setupSpaceConstraint` for more detail.
    """
    return spaceConstraintData['spaces'] + spaceConstraintData['dynamicSpaces']


def _getNextOpenSwitchIndex(spaceConstraintData):
    """
    Return the next available switch index for a space constraint.

    Args:
        spaceConstraintData (dict): The loaded space constraint data
            from the space constraint node
    """
    allSpaces = _getAllSpacesInConstraint(spaceConstraintData)
    allIndeces = sorted([s['index'] for s in allSpaces])

    index = 0
    while index in allIndeces:
        index += 1
    return index


def addDynamicSpace(node, space):
    """
    Add a space dynamically to a space constraint.
    This is intended for use during animation, and is not used
    to setup the native spaces of the constraint.
    """
    pass
