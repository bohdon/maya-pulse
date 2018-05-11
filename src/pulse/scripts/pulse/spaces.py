
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
        follower (PyNode): The node that will be constrained, can be
            different than the control.
        spaceNames (str list): The names of all spaces to be applied
    """

    data = {
        # native spaces in this constraint
        'spaces': [],
        # dynamic spaces (added during animation), which may be
        # from the native rig, or from an external one
        'dynamicSpaces': [],
        # transform that is actually constrained
        'constrainedNode': follower,
        # the addition utility nodes internal to the constraint
        'translateAdd': None,
        'rotateAdd': None,
        'scaleAdd': None,
    }

    # native space indeces always take priority,
    # which means dynamic spaces may be adversely affected
    # if the native spaces change on a published rig
    # TODO: ability to reindex dynamic spaces
    for i, spaceName in enumerate(spaceNames):
        data['spaces'].append({
            'name': spaceName,
            'switch': None,
            'index': i,
        })

    # create addition utilities for transform attrs
    addUtilities = [
        ('t', 'translateAdd'),
        ('r', 'rotateAdd'),
        ('s', 'scaleAdd'),
    ]

    for attrName, metaKey in addUtilities:
        # create addition utility
        defaultVal = 1 if (attrName == 's') else 0
        # create add node with first item set to defaults
        addNode = pulse.utilnodes.add(
            (defaultVal, defaultVal, defaultVal)).node()
        addNode.rename('{0}_add{1}'.format(
            node.nodeName(), attrName.upper()))

        # connect to the follower node
        addNode.output3D >> follower.attr(attrName)

        # store reference to utility in meta data
        data[metaKey] = addNode

    meta.setMetaData(node, SPACECONSTRAINT_METACLASS, data)

    # setup space switching attr
    if not node.hasAttr(SPACESWITCH_ATTR):
        enumNames = ':'.join(spaceNames)
        node.addAttr(SPACESWITCH_ATTR, at='enum', en=enumNames)
        sattr = node.attr(SPACESWITCH_ATTR)
        sattr.setKeyable(True)


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
    Create the actual constraints for each defined space in
    a space constraint node.

    Args:
        node (PyNode): The space constraint node
        spaceNodesByName (dict): A dict of the space
            nodes index by name.
    """
    data = meta.getMetaData(node, SPACECONSTRAINT_METACLASS)
    for spaceData in data['spaces']:
        # ensure the switch is not already created
        if not spaceData['switch']:
            spaceNode = spaceNodesByName.get(spaceData['name'], None)
            if spaceNode:
                _createConstraintSwitchForSpace(
                    node, data, spaceData, spaceNode)
            else:
                LOG.warning(
                    "Space node not found: {0}".format(spaceData['name']))


def _createConstraintSwitchForSpace(node, spaceConstraintData, spaceData, spaceNode):
    """
    Create and connect the conditions and constraints for a space constraint
    connected to a specific space node.

    Args:
        node (PyNode): The space constraint node
        spaceConstraintData (dict): The loaded space constraint data
            from the space constraint node
        spaceData (dict): The dict containing space data for the
            constraint, set during `prepareSpaceConstraint` or
            `addDynamicSpace`
        spaceNode (PyNode): The node representing the space
    """
    spaceAttr = node.attr(SPACESWITCH_ATTR)
    index = spaceData['index']
    nodeName = node.nodeName()

    # create the condition that will control whether
    # the constraints from this space are be active
    # node state 0 == active, 2 == disabled
    stateCndAttr = pulse.utilnodes.equal(spaceAttr, index, 0, 2)
    stateCndNode = stateCndAttr.node()
    stateCndNode.rename('{0}_isSpace{1}Active'.format(nodeName, index))

    # create parent and scale constraints
    follower = spaceConstraintData['constrainedNode']
    pc = createPartialParentConstraint(spaceNode, follower)
    pc.rename('space{0}_parentConstraint'.format(index))
    pm.parentConstraint(spaceNode, pc, e=True, mo=True)
    sc = createPartialScaleConstraint(spaceNode, follower)
    sc.rename('space{0}_scaleConstraints'.format(index))
    for c in (pc, sc):
        stateCndAttr >> c.nodeState

        # TODO: don't lock dynamic space constraints
        pulse.nodes.setConstraintLocked(c, True)

    # create value conditions for each attribute
    valTCndAttr = pulse.utilnodes.equal(
        spaceAttr, index, pc.constraintTranslate, (0, 0, 0))
    valRCndAttr = pulse.utilnodes.equal(
        spaceAttr, index, pc.constraintRotate, (0, 0, 0))
    valSCndAttr = pulse.utilnodes.equal(
        spaceAttr, index, sc.constraintScale, (0, 0, 0))
    valTCndAttr.node().rename('{0}_space{1}_TVal'.format(nodeName, index))
    valRCndAttr.node().rename('{0}_space{1}_RVal'.format(nodeName, index))
    valSCndAttr.node().rename('{0}_space{1}_SVal'.format(nodeName, index))

    # connect to addition nodes
    addTNode = spaceConstraintData['translateAdd']
    addRNode = spaceConstraintData['rotateAdd']
    addSNode = spaceConstraintData['scaleAdd']
    valTCndAttr >> addTNode.input3D[index]
    valRCndAttr >> addRNode.input3D[index]
    valSCndAttr >> addSNode.input3D[index]

    return stateCndNode


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


def createPartialParentConstraint(leader, follower):
    """
    Create a parent constraint node between a leader and follower,
    but do not connect it to the follower node's transform attrs,
    only connect inputs from the two nodes into the constraint.

    Args:
        leader (PyNode): The node that will lead the constraint
        follower (PyNode): The node affected by the constraint
    """

    # create the constraint node
    con = pm.createNode('parentConstraint')
    con.setParent(follower)

    # hiding the constraint prevents camera framing issues if the pivot location is off
    con.visibility.set(0)

    # connect inputs from leader
    leadConnections = {
        't': 'target[0].targetTranslate',
        'r': 'target[0].targetRotate',
        's': 'target[0].targetScale',
        'ro': 'target[0].targetRotateOrder',
        'rp': 'target[0].targetRotatePivot',
        'rpt': 'target[0].targetRotateTranslate',
        'pm[0]': 'target[0].targetParentMatrix',
    }
    if isinstance(leader, pm.nt.Joint):
        leadConnections['jo'] = 'target[0].targetJointOrient'

    for srcname, dstname in leadConnections.items():
        src = leader.attr(srcname)
        dst = con.attr(dstname)
        src >> dst

    # connect inputs from constrained node
    followerConnections = {
        'ro': 'constraintRotateOrder',
        'rp': 'constraintRotatePivot',
        'rpt': 'constraintRotateTranslate',
        'pim[0]': 'constraintParentInverseMatrix',
    }

    for srcname, dstname in followerConnections.items():
        src = follower.attr(srcname)
        dst = con.attr(dstname)
        src >> dst

    return con


def createPartialScaleConstraint(leader, follower):
    """
    Create a scale constraint node between a leader and follower,
    but do not connect it to the follower node's transform attrs,
    only connect inputs from the two nodes into the constraint.

    Args:
        leader (PyNode): The node that will lead the constraint
        follower (PyNode): The node affected by the constraint
    """

    # create the constraint
    con = pm.createNode('scaleConstraint')
    con.setParent(follower)

    # hiding the constraint prevents camera framing issues if the pivot location is off
    con.visibility.set(0)

    # connect inputs from leader
    leaderConnections = {
        's': 'target[0].targetScale',
        'pm[0]': 'target[0].targetParentMatrix',
    }

    for srcname, dstname in leaderConnections.items():
        src = leader.attr(srcname)
        dst = con.attr(dstname)
        src >> dst

    # connect inputs from constrained node
    followerConnections = {
        'pim[0]': 'constraintParentInverseMatrix',
    }

    for srcname, dstname in followerConnections.items():
        src = follower.attr(srcname)
        dst = con.attr(dstname)
        src >> dst

    return con
