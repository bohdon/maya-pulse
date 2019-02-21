"""
Space Switching Constraint Setup
    - Store offsets from each space node in new attrs on the follower
        (follower.wm * space.wm.inverse)
    - Connect all offset matrices to 'offsetChoice' (choice) node
    - Connect all space node world matrices to 'spaceChoice' (choice) node
    - Connect 'space' attribute (enum) to selector of both choice nodes
    - Connect output of choices to calc new follower world matrix (multMatrix)
        (offsetChoice.output * spaceChoice.output * follower.pim)
    - Decompose and connect to follower trs

(see space switching solution by Jarred Love)

"""

import os
import logging
from fnmatch import fnmatch
import pymel.core as pm
import pymetanode as meta

import pulse.nodes
import pulse.utilnodes

__all__ = [
    'addDynamicSpace',
    'createSpaceConstraints',
    'createSpaceConstraint',
    'createSpace',
    'prepareSpaceConstraint',
    'getAllSpaceConstraints',
    'getAllSpaces',
    'getAllSpacesIndexedByName',
    'isSpace',
    'isSpaceConstraint',
]

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


def prepareSpaceConstraint(node, follower, spaceNames):
    """
    Prepare a new space constraint. This sets up the constrained
    node, but does not connect it to the desired spaces until
    `createSpaceConstraint` is called.

    Args:
        node (PyNode): The node that will contain space switching attrs
        follower (PyNode): The node that will be constrained, can be `node`,
            or more commonly, a parent (offset) of `node`.
        spaceNames (str list): The names of all spaces to be applied
    """

    # setup space switching attr
    if not node.hasAttr(SPACESWITCH_ATTR):
        enumNames = ':'.join(spaceNames)
        node.addAttr(SPACESWITCH_ATTR, at='enum', en=enumNames)
        spaceAttr = node.attr(SPACESWITCH_ATTR)
        spaceAttr.setKeyable(True)
    else:
        spaceAttr = node.attr(SPACESWITCH_ATTR)

    nodeName = node.nodeName()

    offsetChoiceName = nodeName + '_space_offset_choice'
    spaceChoiceName = nodeName + '_space_choice'
    multMatrixName = nodeName + '_space_mmtx'
    decompName = nodeName + '_space_decomp'

    # create utility nodes
    offsetChoice = pm.shadingNode('choice', n=offsetChoiceName, asUtility=True)
    spaceChoice = pm.shadingNode('choice', n=spaceChoiceName, asUtility=True)
    pulse.utilnodes.loadMatrixPlugin()
    multMatrix = pm.shadingNode('multMatrix', n=multMatrixName, asUtility=True)
    decomp = pm.shadingNode('decomposeMatrix', n=decompName, asUtility=True)

    # setup connections
    spaceAttr >> offsetChoice.selector
    spaceAttr >> spaceChoice.selector
    offsetChoice.output >> multMatrix.matrixIn[0]
    spaceChoice.output >> multMatrix.matrixIn[1]
    follower.pim >> multMatrix.matrixIn[2]
    multMatrix.matrixSum >> decomp.inputMatrix
    # connection from decomp output to the follower trs
    # occurs after the actual space nodes are connected

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
        'decompose': decomp,
    }

    meta.setMetaData(node, SPACECONSTRAINT_METACLASS, data)


def createSpaceConstraints(nodes):
    """
    Create the actual constraints for a list of prepared
    space constraints. This is more efficient than calling
    createSpaceConstraint for each node since all
    spaces are gathered only once.
    """
    spaceNodesByName = getAllSpacesIndexedByName()

    allConstraints = getAllSpaceConstraints()
    for constraint in allConstraints:
        _createSpaceConstraint(constraint, spaceNodesByName)


def createSpaceConstraint(node):
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
    _createSpaceConstraint(node, spaceNodesByName)


def _createSpaceConstraint(node, spaceNodesByName):
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
                _connectSpaceToConstraint(node, data, index, spaceNode)
                didConnectAny = True
            else:
                LOG.warning(
                    "Space node not found: {0}".format(spaceData['name']))

    if didConnectAny:
        # connect space constraint output now that at least one space is setup
        # TODO: make sure the space 0 is setup, or whatever the attrs value is
        decomp = data['decompose']
        follower = data['follower']
        decomp.outputTranslate >> follower.translate
        decomp.outputRotate >> follower.rotate
        decomp.outputScale >> follower.scale


def _connectSpaceToConstraint(node, spaceConstraintData, index, spaceNode):
    """
    Calculate and store the offset for a space, and connect the space
    to the choice nodes of a space constraint.

    Args:
        node (PyNode): The space constraint node
        spaceConstraintData (dict): The loaded space constraint data
            from the space constraint node
        index (int): The index of the space being connected
        spaceNode (PyNode): The node representing the space
    """
    # calculate and store the offset between the space and follower
    follower = spaceConstraintData['follower']
    offsetMatrix = follower.wm.get() * spaceNode.wm.get().inverse()
    offsetAttrName = 'space{}_offset'.format(index)
    follower.addAttr(offsetAttrName, dt='matrix')
    offsetAttr = follower.attr(offsetAttrName)
    offsetAttr.set(offsetMatrix)

    # connect offset choice
    offsetChoice = spaceConstraintData['offsetChoice']
    offsetAttr >> offsetChoice.input[index]

    # connect space choice
    spaceChoice = spaceConstraintData['spaceChoice']
    spaceNode.wm >> spaceChoice.input[index]


def _getAllSpacesInConstraint(spaceConstraintData):
    """
    Return a combined list of native and dynamic spaces for a constraint.

    Args:
        spaceConstraintData (dict): The loaded space constraint data
            from the space constraint node

    Returns:
        A list of dict representing spaces applied to a constraint.
        See `prepareSpaceConstraint` for more detail.
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
