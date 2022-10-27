import logging
import re
from abc import ABC
from typing import List, Optional, Tuple

import pymel.core as pm

from .blueprints import Blueprint
from .vendor import pymetanode as meta
from . import editorutils
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

def get_all_mirror_nodes():
    """
    Return all nodes that have mirroring data
    """
    return meta.findMetaNodes(MIRROR_METACLASS)


def is_mirror_node(node):
    """
    Return whether a node has mirroring data

    Args:
        node: A PyNode, MObject, or node name
    """
    return meta.hasMetaClass(node, MIRROR_METACLASS)


def validate_mirror_node(node):
    """
    Ensure the node still has a valid mirroring counterpart.
    If it does not, remove the mirror data from the node.

    Return:
        True if the node is a valid mirror node
    """
    if not is_mirror_node(node):
        return False
    data = meta.getMetaData(node, MIRROR_METACLASS)
    other_node = data['otherNode']
    if other_node is None:
        LOG.debug("{0} paired node not found, "
                  "removing mirroring data".format(node))
        meta.removeMetaData(node, MIRROR_METACLASS)
        return False
    else:
        others_other = get_paired_node(other_node, False)
        if others_other != node:
            LOG.debug("{0} pairing is unreciprocated, "
                      "removing mirror data".format(node))
            meta.removeMetaData(node, MIRROR_METACLASS)
            return False
    return True


def cleanup_all_mirror_nodes():
    """
    Remove mirroring metadata from any nodes in the scene
    that are no longer valid (missing their counterpart node).
    """
    for node in get_all_mirror_nodes():
        validate_mirror_node(node)


def pair_mirror_nodes(node_a, node_b):
    """
    Make both nodes associated as mirrors by adding
    mirroring data and a reference to each other.

    Args:
        node_a: A PyNode, MObject, or node name
        node_b: A PyNode, MObject, or node name
    """
    set_mirroring_data(node_a, node_b)
    set_mirroring_data(node_b, node_a)


def unpair_mirror_node(node):
    """
    Unpair the node from any associated mirror node.
    This removes mirroring data from both this
    node and its counterpart.

    Args:
        node: A PyNode, MObject, or node name
    """
    if is_mirror_node(node):
        other_node = get_paired_node(node)
        remove_mirroring_data(node)
        if other_node:
            remove_mirroring_data(other_node)


def duplicate_and_pair_node(source_node):
    """
    Duplicate a node, and pair it with the node that was duplicated.

    Returns:
        The newly created node.
    """
    with preservedSelection():
        dest_node = pm.duplicate([source_node] + source_node.getChildren(s=True), po=True)[0]
        # handle bug in recent maya versions where extra empty
        # transforms will be included in the duplicate
        extra = dest_node.listRelatives(typ='transform')
        if extra:
            LOG.debug("Deleting extra transforms from mirroring: {0}".format(source_node))
            pm.delete(extra)
        # associate nodes
        pair_mirror_nodes(source_node, dest_node)
        return dest_node


def set_mirroring_data(node, other_node):
    """
    Set the mirroring data for a node

    Args:
        node: A node on which to set the mirroring data
        other_node: The counterpart node to be stored in the mirroring data
    """
    data = {
        'otherNode': other_node,
    }
    meta.setMetaData(node, MIRROR_METACLASS, data, undoable=True)


def get_paired_node(node, validate=True):
    """
    For a node with mirroring data, return the other node.

    Args:
        node: A node with mirroring data that references another node
        validate (bool): When true, ensures that the pairing is
            reciprocated by the other node
    """
    if is_mirror_node(node):
        data = meta.getMetaData(node, MIRROR_METACLASS)
        if validate:
            other_node = data['otherNode']
            if other_node and validate:
                if get_paired_node(other_node, False) == node:
                    return other_node
                else:
                    LOG.debug('{0} pairing not reciprocated'.format(node))
        else:
            return data['otherNode']


def remove_mirroring_data(node):
    """
    Remove mirroring data from a node. This does NOT
    remove mirroring data from the other node, if there
    is one. See `unpair_mirror_node` for removing mirroring
    data from two nodes at once.

    Args:
        node: A PyNode, MObject, or node name
    """
    meta.removeMetaData(node, MIRROR_METACLASS)


# Transformations
# ---------------

def is_centered(node, axis=0):
    """
    Return True if the node is centered on a specific world axis.
    """
    axis = nodes.get_axis(axis)
    abs_axis_val = abs(node.getTranslation(space='world')[axis.index])
    return abs_axis_val < MIRROR_THRESHOLD


def get_centered_parent(node, axis=0):
    """
    Return the closest parent node that is centered.
    If no parent nodes are centered, return the highest parent.

    Args:
        node: A PyNode
        axis: The axis on which the node is centered.
    """
    # TODO: use enum for axis values
    this_parent = node.getParent()
    if this_parent is None:
        return
    while this_parent is not None:
        if is_centered(this_parent, axis):
            return this_parent
        last_parent = this_parent
        this_parent = last_parent.getParent()
    return last_parent


def get_mirrored_parent(node):
    """
    Return the closest parent node that has mirroring data.

    Args:
        node: A PyNode
    """
    this_parent = node.getParent()
    if this_parent is None:
        return
    while this_parent is not None:
        if is_mirror_node(this_parent):
            return this_parent
        last_parent = this_parent
        this_parent = last_parent.getParent()
    return last_parent


def get_mirrored_or_centered_parent(node, axis=0):
    """
    Return the closest parent node that is either centered,
    or already paired with another mirroring node.
    """
    center = get_centered_parent(node, axis)
    mirror = get_mirrored_parent(node)
    if center is None:
        return mirror
    if mirror is None:
        return center
    if center.hasParent(mirror):
        return center
    if mirror.hasParent(center):
        return mirror
    return center


def get_best_mirror_mode(node_a, node_b):
    """
    Given two nodes, return the mirror mode that matches
    their current transform relationship.

    Simple performs a loose check to see if the nodes are
    aligned, and if not, returns the Simple mirroring mode.
    """
    awm = nodes.get_world_matrix(node_a)
    bwm = nodes.get_world_matrix(node_b)
    a_axes = nodes.get_closest_aligned_axes(awm)
    b_axes = nodes.get_closest_aligned_axes(bwm)
    if a_axes == b_axes:
        return MirrorMode.Aligned
    return MirrorMode.Simple


class MirrorOperation(object):
    """
    An operation that can be performed when mirroring nodes.
    Receives a call to mirror a source node and target node.
    """

    def __init__(self):
        # the axis to mirror across
        self.axis = 0
        # if set, the custom matrix to use as the base for mirroring
        self.axisMatrix = None

    def mirror_node(self, source_node, dest_node, is_new_node):
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

    def mirror_node(self, source_node, dest_node, is_new_node):
        """
        Change the parent of a dest node to match that of a source node,
        ensuring the use of paired nodes where possible to preserve
        a mirrored parenting structure.

        Handles joint parenting specially by checking for centered
        parents along an axis, as well as connecting inverse scales
        so that segment scale compensate still works.
        """
        with preservedSelection():
            # get parent of source node
            if self.findCenteredJoints and isinstance(source_node, pm.nt.Joint):
                src_parent = get_mirrored_or_centered_parent(source_node, self.axis)
            else:
                src_parent = source_node.getParent()

            if src_parent:
                dst_parent = get_paired_node(src_parent)
                if dst_parent:
                    self._set_parent(dest_node, dst_parent)
                else:
                    self._set_parent(dest_node, src_parent)
            else:
                self._set_parent(dest_node, None)

            # handle joint re-parenting
            if isinstance(dest_node, pm.nt.Joint):
                p = dest_node.getParent()
                if p and isinstance(p, pm.nt.Joint):
                    if not pm.isConnected(p.scale, dest_node.inverseScale):
                        p.scale >> dest_node.inverseScale

    @staticmethod
    def _set_parent(node, parent):
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

    def _kwargs_for_get(self):
        """
        Return kwargs for get_mirror_settings calls
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

    def _kwargs_for_apply(self):
        """
        Return kwargs for apply_mirror_settings calls
        """
        return dict(
            translate=self.setTranslate,
            rotate=self.setRotate,
            scale=self.setScale,
            attrs=self.setAttrs,
        )

    def mirror_node(self, source_node, dest_node, is_new_node):
        """
        Move a node to the mirrored position of another node.

        Args:
            source_node (PyNode): The node whos position will be used
            dest_node (PyNode): The node to modify
            is_new_node (bool): Is the destination node newly created?
        """
        if self.mirrorRotateOrder:
            dest_node.rotateOrder.set(source_node.rotateOrder.get())

        settings = get_mirror_settings(source_node, dest_node, **self._kwargs_for_get())
        if settings:
            apply_mirror_settings(settings, **self._kwargs_for_apply())

    def _prepare_flip(self, source_node, dest_node):
        """
        Return settings gathered in preparation for flipping two nodes.
        """
        source_settings = get_mirror_settings(source_node, dest_node, **self._kwargs_for_get())
        dest_settings = get_mirror_settings(dest_node, source_node, **self._kwargs_for_get())
        return source_settings, dest_settings

    def _apply_flip(self, flip_data):
        """
        Apply the flip data gathered from `_prepare_flip,` which will
        move the nodes to their flipped locations.
        """
        source_settings, dest_settings = flip_data
        if source_settings and dest_settings:
            apply_mirror_settings(source_settings, **self._kwargs_for_apply())
            apply_mirror_settings(dest_settings, **self._kwargs_for_apply())

    def flip(self, source_node, dest_node):
        """
        Flip the transforms of two nodes such that each
        node moves to the mirrored transform of the other.
        """
        flip_data = self._prepare_flip(source_node, dest_node)
        self._apply_flip(flip_data)

    def flip_multiple(self, node_pairs):
        """
        Perform `flip` on multiple nodes, by gathering first
        and then applying second, in order to avoid parenting
        and dependency issues.

        Args:
            node_pairs (list): A list of 2-tuple PyNodes representing
                (source, dest) node for each pair.
        """
        flip_data_list = []
        for (source, dest) in node_pairs:
            flip_data = self._prepare_flip(source, dest)
            flip_data_list.append(flip_data)

        for flip_data in flip_data_list:
            self._apply_flip(flip_data)

    def flip_center(self, nodes):
        """
        Move one or more non-mirrored nodes to the mirrored position
        of its current transform. The node list should be in order of
        dependency, where parents are first, followed by children in
        hierarchical order.
        """
        settings = []

        for n in nodes:
            kwargs = self._kwargs_for_get()
            kwargs['mirrorMode'] = MirrorMode.Aligned
            kwargs['excludedNodeSettings'] = ['mirrorMode']
            s = get_mirror_settings(n, n, **kwargs)
            settings.append(s)

        # TODO: attempt to automatically handle parent/child relationships
        #       to lift the requirement of giving nodes in hierarchical order
        for s in settings:
            apply_mirror_settings(s, **self._kwargs_for_apply())


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

    def mirror_node(self, source_node, dest_node, is_new_node):
        # curve shape mirroring doesn't care about the actual
        # position, its only job is to flip the curve
        if is_new_node:
            MirrorCurveShapes.flip_all_curve_shapes(dest_node, self.axis, self.mirrorMode)
        elif self.replaceExistingShapes:
            self.replace_curve_shapes(source_node, dest_node)
            MirrorCurveShapes.flip_all_curve_shapes(dest_node, self.axis, self.mirrorMode)

    @staticmethod
    def flip_all_curve_shapes(node, axis=0, mirrorMode=MirrorMode.Simple):
        """
        Flip the position of all cvs in all curve shapes of a node
        in a manner that corresponds to the transformation mirror modes.

        Args:
            node (NurbsCurve): The node to mirror
            axis (int): An axis to mirror across
            mirrorMode: The MirrorMode type to use
        """
        shapes = node.getChildren(s=True)
        for shape in shapes:
            if hasattr(shape, "cv"):
                MirrorCurveShapes.flip_curve_shape(shape, axis, mirrorMode)

    @staticmethod
    def flip_curve_shape(curve_shape, axis=0, mirrorMode=MirrorMode.Simple):
        """
        Flip the position of all cvs in a curve shape in a manner that
        corresponds to the transformation mirror modes.

        Args:
            curve_shape (NurbsCurve): The curve to mirror
            axis (int): An axis to mirror across
            mirrorMode: The MirrorMode type to use
        """
        if mirrorMode == MirrorMode.Simple:
            pm.scale(curve_shape.cv, [-1, -1, -1])
        elif mirrorMode == MirrorMode.Aligned:
            s = [1, 1, 1]
            s[axis] = -1
            pm.scale(curve_shape.cv, s)

    def replace_curve_shapes(self, source_node, dest_node):
        """
        Copy the curve shapes from one node to another, clearing out any curve shapes
        in the destination node first.

        Args:
            source_node (pm.PyNode): The source node to copy shapes from
            dest_node (pm.PyNode): The destination node to copy shapes to
        """
        dst_shapes = dest_node.getShapes(type=self.shapeTypes)
        if dst_shapes:
            pm.delete(dst_shapes)

        src_shapes = source_node.getShapes(type=self.shapeTypes)
        for shape in src_shapes:
            dupe = pm.duplicate(shape, addShape=True)
            pm.parent(dupe, dest_node, shape=True, relative=True)


class MirrorJointDisplay(MirrorOperation):
    """
    Mirrors the display settings of joints
    """

    def mirror_node(self, source_node, dest_node, is_new_node):
        if source_node.type() == 'joint' and dest_node.type() == 'joint':
            dest_node.radius.set(source_node.radius.get())


class BlueprintMirrorOperation(MirrorOperation, ABC):
    """
    A MirrorOperation that makes use of a Blueprint config
    """

    def __init__(self):
        super(BlueprintMirrorOperation, self).__init__()
        # the Blueprint owner of the mirror operation
        self.blueprint: Optional[Blueprint] = None
        # the Blueprint's config data
        self._config: Optional[dict] = None

    def get_config(self):
        """
        Return the Blueprint's config. Caches the config
        on the first request.
        """
        if self._config is None:
            if self.blueprint:
                self._config = self.blueprint.get_config()
        return self._config


def _create_name_replacement(search, replace):
    """
    Return a tuple containing a regex and replacement string.
    Regexes replace prefixes, suffixes, or middles, as long as
    the search is separated with '_' from adjacent characters.
    """
    regex = re.compile(f'(?<![^_]){search}(?=(_|$))')
    return regex, replace


def _generate_mirror_name_replacements(config):
    """
    Generate and return the full list of replacement pairs.

    Returns:
        A list of (regex, replacement) tuples.
    """
    replacements = []
    sym_config = config.get('symmetry', {})
    pairs = sym_config.get('pairs', [])

    for pair in pairs:
        if 'left' in pair and 'right' in pair:
            left = pair['left']
            right = pair['right']
            l2r = _create_name_replacement(left, right)
            r2l = _create_name_replacement(right, left)
            replacements.append(l2r)
            replacements.append(r2l)
        else:
            LOG.warning("Invalid symmetry pairs")

    return replacements


def _get_mirrored_name_with_replacements(name, replacements):
    mirrored_name = name
    for regex, repl in replacements:
        if regex.search(mirrored_name):
            mirrored_name = regex.sub(repl, mirrored_name)
            break
    return mirrored_name


def get_mirrored_name(name, config):
    """
    Given a string name, return the mirrored version considering
    all symmetry names defined in the Blueprint config.
    """
    replacements = _generate_mirror_name_replacements(config)
    return _get_mirrored_name_with_replacements(name, replacements)


class MirrorNames(BlueprintMirrorOperation):
    """
    Mirrors the names of nodes.
    """

    def __init__(self):
        super(MirrorNames, self).__init__()
        # cached set of (regex, replacement) pairs
        self._replacements = None

    def _get_replacements(self):
        """
        Return the list of regex and replacement pairs.
        Caches the list the first time it is requested so that
        subsequent calls are faster.
        """
        if self._replacements is None:
            self._replacements = _generate_mirror_name_replacements(self.get_config())
        return self._replacements

    def mirror_node(self, source_node, dest_node, is_new_node):
        name = source_node.nodeName()
        dest_name = _get_mirrored_name_with_replacements(name, self._get_replacements())
        dest_node.rename(dest_name)


class MirrorColors(BlueprintMirrorOperation):
    """
    Mirrors the override display color of nodes.
    """

    def __init__(self):
        super(MirrorColors, self).__init__()
        # cached set of (regex, replacement) pairs
        self._replacements = None

    def _get_replacements(self):
        """
        Return the list of regex and replacement pairs.
        Caches the list the first time it is requested so that
        subsequent calls are faster.
        """
        if self._replacements is None:
            self._replacements = _generate_mirror_name_replacements(self.get_config())
        return self._replacements

    def mirror_node(self, source_node, dest_node, is_new_node):
        source_color = nodes.get_override_color(source_node)
        if source_color:
            # get name of source color
            source_name = editorutils.getColorName(source_color)
            if source_name:
                # mirror the name
                dest_name = _get_mirrored_name_with_replacements(source_name, self._get_replacements())
                # get color of mirrored name
                dest_color = editorutils.getNamedColor(dest_name)
                if dest_color:
                    nodes.set_override_color(dest_node, tuple(dest_color))


class MirrorLinks(BlueprintMirrorOperation):
    """
    Mirrors Blueprint links. See links.py
    """

    def mirror_node(self, source_node, dest_node, is_new_node):
        # get link meta data
        source_link_data = links.getLinkMetaData(source_node)
        dest_link_data = links.getLinkMetaData(dest_node)

        if source_link_data:
            # if no destination link data already exists, create
            # a copy of the source link data, otherwise only affect the target node
            if not dest_link_data:
                dest_link_data = source_link_data

            # TODO: provide a layer of abstraction, mirroring shouldn't have to know the details

            source_target_nodes = source_link_data.get('targetNodes')
            if source_target_nodes:
                dest_target_nodes = [get_paired_node(n) for n in source_target_nodes]
                if dest_target_nodes:
                    dest_link_data['targetNodes'] = dest_target_nodes
                    links.setLinkMetaData(dest_node, dest_link_data)

            # position the dest node using the link
            links.applyLinkPosition(dest_node)

        elif dest_link_data:
            # remove link data from dest node
            links.unlink(dest_node)


class MirrorUtil(object):
    """
    A util class for performing MirrorOperations.
    Provides functionality for duplicating nodes that aren't paired,
    as well as performing the operations recursively on a node and
    all of its children.
    """

    def __init__(self):
        # the list of mirror operations to run, use add_operation
        self._operations: List[MirrorOperation] = []

        # the axis to mirror across
        self.axis = 0
        # if set, the custom matrix to use as the base for mirroring
        self.axisMatrix = None

        # don't mirror nodes that are centered along the mirror axis
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

    def add_operation(self, operation):
        self._operations.append(operation)

    def run(self, source_nodes):
        """
        Run all mirror operations on the given source nodes.
        """
        filtered_nodes = self.gather_nodes(source_nodes)
        pairs = self.create_node_pairs(filtered_nodes)
        for operation in self._operations:
            # ensure consistent mirroring settings for all operations
            self.configure_operation(operation)
            for pair in pairs:
                is_new_node = pair[1] in self._newNodes
                operation.mirror_node(pair[0], pair[1], is_new_node)
        self._newNodes = []

    def should_mirror_node(self, source_node) -> bool:
        """
        Return whether the node sould be mirrored, or skipped.

        Accounts for special situations like centered joints,
        which may be included with recursive operations, but not
        wanted when mirroring.
        """
        if self.skipCentered:
            if is_centered(source_node, self.axis):
                return False

        return True

    def configure_operation(self, operation):
        """
        Configure a MirrorOperation instance.
        """
        operation.axis = self.axis
        operation.axisMatrix = self.axisMatrix

    def gather_nodes(self, source_nodes):
        """
        Return a filtered and expanded list of source nodes to be mirrored,
        including children if isRecursive is True, and filtering nodes that
        should not be mirrored.
        """
        result = []

        if self.isRecursive:
            source_nodes = nodes.get_parent_nodes(source_nodes)

        # expand to children
        for sourceNode in source_nodes:
            if sourceNode not in result:
                if self.should_mirror_node(sourceNode):
                    result.append(sourceNode)

            if self.isRecursive:
                children = nodes.get_descendants_top_to_bottom(
                    sourceNode, type=['transform', 'joint'])

                for child in children:
                    if child not in result:
                        if self.should_mirror_node(child):
                            result.append(child)

        return result

    def create_node_pairs(self, source_nodes):
        """
        Iterate over a list of source nodes and retrieve or create
        destination nodes using pairing.
        """
        pairs = []

        for sourceNode in source_nodes:
            if self.validateNodes:
                validate_mirror_node(sourceNode)

            if self.isCreationAllowed:
                dest_node, is_new_node = self._get_or_create_pair_node(sourceNode)
                if dest_node and is_new_node:
                    self._newNodes.append(dest_node)
            else:
                dest_node = get_paired_node(sourceNode)

            if dest_node:
                pairs.append((sourceNode, dest_node))
            else:
                LOG.warning("Could not get pair node for: "
                            "{0}".format(sourceNode))

        return pairs

    def _get_or_create_pair_node(self, source_node) -> Tuple[pm.nt.Transform, bool]:
        """
        Return the pair node of a node, and if none exists, create a new pair node.
        Does not check isCreationAllowed.

        Returns:
            The pair node (PyNode), and a bool that is True if the node was just created, False otherwise.
        """
        dest_node = get_paired_node(source_node)
        if dest_node:
            return dest_node, False
        else:
            dest_node = duplicate_and_pair_node(source_node)
            return dest_node, True

    def get_or_create_pair_node(self, source_node) -> pm.nt.Transform:
        """
        Return the pair node of a node, and if none exists,
        create a new pair node. Does not check isCreationAllowed.
        """
        return self._get_or_create_pair_node(source_node)[0]


def get_mirror_settings(sourceNode, destNode=None, useNodeSettings=True, excludedNodeSettings=None, **kwargs):
    """
    Get mirror settings that represent mirroring from a source node to a target node.

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
        See 'get_mirrored_matrices' for a list of kwargs that can be given
        `mirroredAttrs` -- A list of custom attribute names that will
            be included when mirroring
        `customMirrorAttrExps` -- a dictionary of {attr: expression} that
            are evaluated using the given source node and dest node to determine
            custom mirroring behaviour for any attributes
    """

    def filter_node_settings(settings):
        if excludedNodeSettings:
            return {k: v for k, v in settings.items()
                    if k not in excludedNodeSettings}
        return settings

    result = {}

    LOG.debug("Getting Mirror Settings: {0}".format(sourceNode))
    if not destNode:
        destNode = get_paired_node(sourceNode)
    if not destNode:
        return

    # if enabled, pull some custom mirroring settings from the node,
    # these are stored in a string attr as a python dict
    if useNodeSettings:
        data = meta.getMetaData(sourceNode, MIRROR_METACLASS)
        custom_settings = data.get('customSettings')
        if custom_settings is not None:
            LOG.debug("Custom Mirror Node")
            # nodeStngs = data['customSettings']
            LOG.debug("Settings: {0}".format(custom_settings))
            kwargs.update(filter_node_settings(custom_settings))

    # pull some kwargs used for get_mirrored_matrices
    matrix_kwargs = dict([(k, v) for k, v in kwargs.items() if k in (
        'axis', 'axisMatrix', 'translate', 'rotate', 'mirrorMode')])
    result['matrices'] = get_mirrored_matrices(sourceNode, **matrix_kwargs)

    # add list of mirrored attributes as designated by kwargs
    mir_attr_kwargs = dict([(a, getattr(sourceNode, a).get())
                            for a in kwargs.get('mirroredAttrs', [])])
    result.setdefault('mirroredAttrs', {}).update(mir_attr_kwargs)

    for attr, exp in kwargs.get('customMirrorAttrExps', {}).items():
        if exp:
            LOG.debug("Attr: {0}".format(attr))
            LOG.debug("Exp:\n{0}".format(exp))
            val = eval_custom_mirror_attr_exp(
                sourceNode, destNode, attr, exp)
            LOG.debug("Result: {0}".format(val))
            # Eval from the mirror to the dest
            result['mirroredAttrs'][attr] = val

    LOG.debug("Mirrored Attrs: {0}".format(result['mirroredAttrs']))

    # Save additional variables
    result['sourceNode'] = sourceNode
    result['destNode'] = destNode

    return result


def apply_mirror_settings(mirror_settings, translate=True, rotate=True, scale=True, attrs=True):
    """
    Apply mirror settings created from get_mirror_settings
    """
    LOG.debug("Applying Mirror Settings: {0}".format(mirror_settings['destNode']))
    settings = mirror_settings
    if any([translate, rotate, scale]):
        set_mirrored_matrices(settings['destNode'], settings['matrices'],
                              translate=translate, rotate=rotate, scale=scale)

    if attrs:
        LOG.debug("Applying Mirrored Attrs")
        for attrName, val in mirror_settings.get('mirroredAttrs', {}).items():
            LOG.debug("{0} -> {1}".format(attrName, val))
            attr = settings['destNode'].attr(attrName)
            attr.set(val)


CUSTOM_EXP_FMT = """\
def exp():
    {body}return {lastLine}
result = exp()
"""


def eval_custom_mirror_attr_exp(source_node, dest_node, attr, exp):
    LOG.debug("Raw Exp: {0}".format(repr(exp)))

    _globals = {
        'node': source_node,
        'dest_node': dest_node
    }

    if hasattr(source_node, attr):
        _globals['value'] = getattr(source_node, attr).get()
    else:
        raise KeyError(
            "{0} missing mirrored attr {1}".format(source_node, attr))
    if hasattr(dest_node, attr):
        _globals['dest_value'] = getattr(dest_node, attr).get()
    else:
        raise KeyError("{0} missing mirrored attr {1}".format(dest_node, attr))

    # Add a return to the last line of the expression, so we can treat it as a function
    body = [l for l in exp.strip().split('\n') if l]
    last_line = body.pop(-1)
    _exp = CUSTOM_EXP_FMT.format(
        body='\n\t'.join(body + ['']), lastLine=last_line)

    # TODO: do this without exec
    exec(_exp, _globals)
    result = _globals['result']

    return result


def get_mirrored_matrices(node, axis=0, axisMatrix=None, translate=True, rotate=True, mirrorMode=MirrorMode.Simple):
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
        result['matrices'] = get_mirrored_joint_matrices(*jmatrices, **kwargs)
    else:
        result['type'] = 'node'
        result['matrices'] = [get_mirrored_transform_matrix(
            nodes.get_world_matrix(node), **kwargs)]
    return result


def set_mirrored_matrices(node, mirroredMatrices, translate=True, rotate=True, scale=True):
    """
    Set the world matrix for the given node using the given mirrored matrices
    Automatically interprets Transform vs. Joint matrix settings
    """
    if mirroredMatrices['type'] == 'joint':
        LOG.debug("Applying Joint Matrices")
        joints.setJointMatrices(node, *mirroredMatrices['matrices'], translate=translate, rotate=rotate)
    else:
        LOG.debug("Applying Transform Matrix")
        nodes.set_world_matrix(node, *mirroredMatrices['matrices'], translate=translate, rotate=rotate, scale=scale)


def get_mirrored_transform_matrix(matrix, axis=0, axisMatrix=None, translate=True, rotate=True,
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
    axis = nodes.get_axis(axis)
    if axisMatrix is not None:
        # remove scale from the axisMatrix
        axisMatrix = nodes.get_scale_matrix(
            axisMatrix).inverse() * axisMatrix
        matrix = matrix * axisMatrix.inverse()
    s = nodes.get_scale_matrix(matrix)
    r = nodes.get_rotation_matrix(matrix)
    t = matrix[3]
    if translate:
        # negate translate vector
        t[axis.index] = -t[axis.index]
    if rotate:
        r = invert_other_axes(r, axis)
        if mirrorMode == MirrorMode.Aligned:
            LOG.debug("Counter Rotating because mirror mode is Aligned")
            r = counter_rotate_for_non_mirrored(r, axis)
    mirror = s * r
    mirror[3] = t
    if axisMatrix is not None:
        mirror = mirror * axisMatrix
    return mirror


def get_mirrored_joint_matrices(matrix, r, ra, jo, axis=0, axisMatrix=None,
                                translate=True, rotate=True, mirrorMode=MirrorMode.Simple):
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
    mirror = get_mirrored_transform_matrix(
        matrix, axis, axisMatrix, translate, rotate)
    if rotate:
        if axisMatrix is not None:
            # matches orientation with jo
            inv_scale_mtx = nodes.get_scale_matrix(axisMatrix).inverse()
            axisMatrix = inv_scale_mtx * axisMatrix
            jo = jo * axisMatrix.inverse()
        # flips orientation
        jo = invert_other_axes(jo, axis)
        if mirrorMode == MirrorMode.Aligned:
            LOG.debug("Counter Rotating because mirror mode is Aligned")
            # changes orientation to inverted world
            jo = counter_rotate_for_mirrored_joint(jo)
        if axisMatrix is not None:
            # doesn't seem to do anything
            jo = jo * axisMatrix
    return mirror, r, ra, jo


def invert_other_axes(matrix, axis=0):
    """
    Invert the other axes of the given rotation
    matrix based on rows of the matrix.
    """
    axis = nodes.get_axis(axis)
    others = nodes.get_other_axes(axis)
    x, y, z = matrix[:3]
    for v in (x, y, z):
        for a in others:
            v[a.index] *= -1
    return pm.dt.Matrix(x, y, z)


def counter_rotate_for_non_mirrored(matrix, axis=0):
    """
    Essentially rotates 180 on the given axis,
    this is used to create mirroring when ctls
    are set up to not be mirrored at rest pose.
    """
    axis = nodes.get_axis(axis)
    others = [o.index for o in nodes.get_other_axes(axis)]
    x, y, z = matrix[:3]
    for i, row in enumerate((x, y, z)):
        if i in others:
            for col in range(3):
                row[col] *= -1
    return pm.dt.Matrix(x, y, z)


def counter_rotate_for_mirrored_joint(matrix):
    """
    Essentially rotates 180 on the given axis,
    this is used to create mirroring when ctls
    are set up to not be mirrored at rest pose.
    """
    x, y, z = matrix[:3]
    for row in (x, y, z):
        for col in range(3):
            row[col] *= -1
    return pm.dt.Matrix(x, y, z)
