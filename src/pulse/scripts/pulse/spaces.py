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
from typing import Union

import maya.cmds as cmds
import pymel.core as pm

from .vendor import pymetanode as meta
from . import nodes
from . import utilnodes

LOG = logging.getLogger(__name__)

SPACE_METACLASS = 'pulse_space'
SPACE_CONSTRAINT_METACLASS = 'pulse_space_con'
SPACE_SWITCH_ATTR = 'space'


def get_all_spaces():
    """
    Return a list of all space nodes
    """
    return meta.findMetaNodes(SPACE_METACLASS)


def get_all_spaces_indexed_by_name():
    """
    Return all space nodes in a dict indexed by their space name
    """
    all_space_nodes = get_all_spaces()
    result = {}
    for spaceNode in all_space_nodes:
        space_data = meta.getMetaData(spaceNode, SPACE_METACLASS)
        result[space_data['name']] = spaceNode
    return result


def is_space(node):
    """
    Return True if the node is a space

    Args:
        node: A PyNode or string node name
    """
    return meta.hasMetaClass(node, SPACE_METACLASS)


def get_all_space_constraints():
    """
    Return a list of all space constrained nodes
    """
    return meta.findMetaNodes(SPACE_CONSTRAINT_METACLASS)


def is_space_constraint(node):
    """
    Return True if the node is space constrained

    Args:
        node: A PyNode or string node name
    """
    return meta.hasMetaClass(node, SPACE_CONSTRAINT_METACLASS)


def create_space(node: Union[pm.PyNode, str], name: str):
    """
    Create a new space

    Args:
        node: A PyNode or string node name.
        name: A string name of the space to create
    """
    data = {
        'name': name,
    }
    meta.setMetaData(node, SPACE_METACLASS, data)


def setup_space_constraint(node, space_names, follower=None, use_offset_matrix=True):
    """
    Set up a node to be constrained for a space switch, but do not
    actually connect it to the desired spaces until `connect_space_constraint` is called.
    This is necessary because the transforms that represent each space may not
    have been defined yet, but the desire to constrain to them by space name can be expressed
    ahead of time.

    Args:
        node (PyNode): The node that will contain space switching attrs
        space_names (str list): The names of all spaces to be applied
        follower (PyNode): If given, the node that will be constrained, otherwise
            `node` will be used. Useful when wanting to create the space constrain attributes
            on an animation control, but connect the actual constraint to a parent transform
        use_offset_matrix (bool): When true, will connect to the offsetParentMatrix
            of the follower node, instead of directly into the translate, rotate, and scale.
            This also eliminates the necessity for a decompose matrix node.
    """
    if use_offset_matrix and cmds.about(api=True) < 20200000:
        # not supported before Maya 2020
        use_offset_matrix = False

    if not follower:
        follower = node

    # setup space switching attr
    if not node.hasAttr(SPACE_SWITCH_ATTR):
        enum_names = ':'.join(space_names)
        node.addAttr(SPACE_SWITCH_ATTR, at='enum', en=enum_names)
        space_attr = node.attr(SPACE_SWITCH_ATTR)
        space_attr.setKeyable(True)
    else:
        space_attr = node.attr(SPACE_SWITCH_ATTR)

    node_name = node.nodeName()

    offset_choice_name = f'{node_name}_spaceOffset_choice'
    space_choice_name = f'{node_name}_space_choice'
    mult_matrix_name = f'{node_name}_space_mmtx'
    decomp_name = f'{node_name}_space_decomp'

    # create utility nodes
    offset_choice = pm.shadingNode('choice', n=offset_choice_name, asUtility=True)
    space_choice = pm.shadingNode('choice', n=space_choice_name, asUtility=True)
    utilnodes.load_matrix_plugin()
    mult_matrix = pm.shadingNode('multMatrix', n=mult_matrix_name, asUtility=True)
    if not use_offset_matrix:
        decomp = pm.shadingNode(
            'decomposeMatrix', n=decomp_name, asUtility=True)

    # setup connections
    space_attr >> offset_choice.selector
    space_attr >> space_choice.selector
    offset_choice.output >> mult_matrix.matrixIn[0]
    space_choice.output >> mult_matrix.matrixIn[1]
    # follower.pim >> multMatrix.matrixIn[2]
    if not use_offset_matrix:
        mult_matrix.matrixSum >> decomp.inputMatrix
    # final connection to the follower occurs
    # during connect_space_constraint.

    space_data = []
    # native space indeces always take priority,
    # which means dynamic spaces may be adversely affected
    # if the native spaces change on a published rig
    # TODO: ability to reindex dynamic spaces
    for i, spaceName in enumerate(space_names):
        space_data.append({
            'name': spaceName,
            # TODO: is `switch` needed anymore?
            'switch': None,
            'index': i,
        })

    data = {
        # native spaces in this constraint
        'spaces': space_data,
        # dynamic spaces (added during animation), which may be
        # from the native rig, or from an external one
        'dynamicSpaces': [],
        # transform that is actually driven by the space constraint
        'follower': follower,
        # the utility nodes that make up the space constraint
        'offsetChoice': offset_choice,
        'spaceChoice': space_choice,
        'multMatrix': mult_matrix,
        'useOffsetMatrix': use_offset_matrix,
    }
    if not use_offset_matrix:
        # decomp only exists when not using offset matrix
        data['decompose'] = decomp

    meta.setMetaData(node, SPACE_CONSTRAINT_METACLASS, data)


def _setup_space_constraint_attrs(node, space_names):
    # setup space switching attr
    if not node.hasAttr(SPACE_SWITCH_ATTR):
        enum_names = ':'.join(space_names)
        node.addAttr(SPACE_SWITCH_ATTR, at='enum', en=enum_names)
        space_attr = node.attr(SPACE_SWITCH_ATTR)
    else:
        space_attr = node.attr(SPACE_SWITCH_ATTR)
    space_attr.setKeyable(True)


def connect_space_constraints(nodes):
    """
    Create the actual constraints for a list of prepared space constraints.
    This is more efficient than calling connect_space_constraint for each node since all
    spaces are gathered only once.
    """
    space_nodes_by_name = get_all_spaces_indexed_by_name()

    all_constraints = get_all_space_constraints()
    for constraint in all_constraints:
        _connect_space_constraint(constraint, space_nodes_by_name)


def connect_space_constraint(node):
    """
    Create the actual constraints for each defined space in
    a space constraint node.

    Args:
        node (PyNode): The space constraint node
    """
    if not is_space_constraint(node):
        # TODO: warn
        return

    space_nodes_by_name = get_all_spaces_indexed_by_name()
    _connect_space_constraint(node, space_nodes_by_name)


def _connect_space_constraint(node, space_nodes_by_name):
    """
    Connect all spaces defined in the node's space data
    to the space constraint utility nodes.

    Args:
        node (PyNode): The space constraint node
        space_nodes_by_name (dict): A dict of the space
            nodes index by name.
    """
    data = meta.getMetaData(node, SPACE_CONSTRAINT_METACLASS)
    did_connect_any = False
    for spaceData in data['spaces']:
        index = spaceData['index']
        # ensure the switch is not already created
        if not spaceData['switch']:
            space_node = space_nodes_by_name.get(spaceData['name'], None)
            if space_node:
                _connect_space_to_constraint(data, index, space_node)
                did_connect_any = True
            else:
                LOG.warning("Space node not found: %s", spaceData['name'])

    if did_connect_any:
        # connect final output now that at least one space is connected
        # TODO: make sure the space 0 is setup, or whatever the attrs value is
        follower = data['follower']
        use_offset_matrix = data['useOffsetMatrix']

        if use_offset_matrix:
            mult_matrix = data['multMatrix']
            nodes.connectMatrix(mult_matrix.matrixSum, follower, nodes.ConnectMatrixMethod.CONNECT_ONLY)
        else:
            # TODO: support joint matrix constraints that don't disable inheritsTransform,
            #       or just remove this path altogether
            decomp = data['decompose']
            decomp.outputTranslate >> follower.translate
            decomp.outputRotate >> follower.rotate
            decomp.outputScale >> follower.scale
            # no longer need to inherit transform
            follower.inheritsTransform.set(False)


def _connect_space_to_constraint(space_constraint_data, index, space_node):
    """
    Connect a space node to a space constraint choice and calculate the
    preserved offset matrix for the space as well.

    Args:
        space_constraint_data (dict): The loaded space constraint data
            from the space constraint node
        index (int): The index of the space being connected
        space_node (PyNode): The node representing the space
    """
    # connect space node world matrix to choice node
    space_choice = space_constraint_data['spaceChoice']
    space_node.wm >> space_choice.input[index]

    # calculate the offset between the space and follower
    follower = space_constraint_data['follower']
    use_offset_matrix = space_constraint_data['useOffsetMatrix']
    if use_offset_matrix:
        # calculate an offset matrix that doesn't include the local matrix of the follower,
        # so that the result can be plugged into the offsetParentMatrix of the follower
        offset_mtx = follower.pm.get() * space_node.wim.get()
    else:
        # the space constraint will go directly into the transform attrs of the follower,
        # so it should include the follower's world matrix
        offset_mtx = follower.wm.get() * space_node.wim.get()

    # store the offset matrix on the offset choice node
    offset_choice = space_constraint_data['offsetChoice']
    # create a matrix attribute on the choice node to hold the offset
    # (the choice input attributes are wildcards and cannot hold matrix data)
    offset_attr_name = f'offset{index}'
    offset_choice.addAttr(offset_attr_name, dt='matrix')
    offset_attr = offset_choice.attr(offset_attr_name)
    offset_attr.set(offset_mtx)
    offset_attr >> offset_choice.input[index]


def _get_all_spaces_in_constraint(space_constraint_data):
    """
    Return a combined list of native and dynamic spaces for a constraint.

    Args:
        space_constraint_data (dict): The loaded space constraint data
            from the space constraint node

    Returns:
        A list of dict representing spaces applied to a constraint.
        See `setup_space_constraint` for more detail.
    """
    return space_constraint_data['spaces'] + space_constraint_data['dynamicSpaces']


def _get_next_open_switch_index(space_constraint_data):
    """
    Return the next available switch index for a space constraint.

    Args:
        space_constraint_data (dict): The loaded space constraint data
            from the space constraint node
    """
    all_spaces = _get_all_spaces_in_constraint(space_constraint_data)
    all_indeces = sorted([s['index'] for s in all_spaces])

    index = 0
    while index in all_indeces:
        index += 1
    return index


def add_dynamic_space(node, space):
    """
    Add a space dynamically to a space constraint.
    This is intended for use during animation, and is not used
    to set up the native spaces of the constraint.
    """
    pass
