import logging
import re
from abc import ABC
from copy import copy
from typing import List, Optional, Tuple

import pymel.core as pm

from .blueprints import Blueprint
from .build_items import BuildActionProxy, BuildActionAttribute, BuildActionAttributeType
from .vendor import pymetanode as meta
from . import editor_utils
from . import joints
from . import links
from . import nodes
from .vendor.mayacoretools import preservedSelection
from .vendor.overrides import overrides

LOG = logging.getLogger(__name__)

MIRROR_METACLASS = "pulse_mirror"

MIRROR_THRESHOLD = 0.0001

CUSTOM_EXP_FMT = """\
def exp():
    {body}return {lastLine}
result = exp()
"""


class MirrorMode(object):
    """
    Contains constants representing the available types of mirroring

    SIMPLE:
        a ctl is mirrored across a single axis in the tranditional
        sense, this means the non-mirror axis basis vectors are flipped

    ALIGNED:
        a ctl is mirrored across a single axis in a visual sense,
        but the relationship between the matrices is more complicated.
        The result is an orientation that looks the same on both
        sides of an axis, as if they matched in world space in rest pose
    """

    SIMPLE = "simple"
    ALIGNED = "aligned"


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
    other_node = data["otherNode"]
    if other_node is None:
        LOG.debug("%s paired node not found, removing mirroring data", node)
        meta.removeMetaData(node, MIRROR_METACLASS)
        return False
    else:
        others_other = get_paired_node(other_node, False)
        if others_other != node:
            LOG.debug("%s pairing is not reciprocated, removing mirror data", node)
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
        extra = dest_node.listRelatives(typ="transform")
        if extra:
            LOG.debug("Deleting extra transforms from mirroring: %s", source_node)
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
        "otherNode": other_node,
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
            other_node = data["otherNode"]
            if other_node and validate:
                if get_paired_node(other_node, False) == node:
                    return other_node
                else:
                    LOG.debug("%s pairing not reciprocated", node)
        else:
            return data["otherNode"]


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


def is_centered(node, axis=0):
    """
    Return True if the node is centered on a specific world axis.
    """
    axis = nodes.get_axis(axis)
    abs_axis_val = abs(node.getTranslation(space="world")[axis.index])
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

    SIMPLE performs a loose check to see if the nodes are
    aligned, and if not, returns the SIMPLE mirroring mode.
    """
    awm = nodes.get_world_matrix(node_a)
    bwm = nodes.get_world_matrix(node_b)
    a_axes = nodes.get_closest_aligned_axes(awm)
    b_axes = nodes.get_closest_aligned_axes(bwm)
    if a_axes == b_axes:
        return MirrorMode.ALIGNED
    return MirrorMode.SIMPLE


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

    def mirror_node(self, source_node: pm.nt.Transform, dest_node: pm.nt.Transform, is_new_node: bool):
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

    @overrides
    def mirror_node(self, source_node: pm.nt.Transform, dest_node: pm.nt.Transform, is_new_node: bool):
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
        self.params = MirrorParams()

    @overrides
    def mirror_node(self, source_node: pm.nt.Transform, dest_node: pm.nt.Transform, is_new_node: bool):
        """
        Move a node to the mirrored position of another node.

        Args:
            source_node: The node whose position will be used.
            dest_node: The node to modify.
            is_new_node: Is the destination node newly created?
        """
        if self.params.mirror_rotate_order:
            dest_node.rotateOrder.set(source_node.rotateOrder.get())

        mirror_data = get_mirror_data(source_node, dest_node, self.params)
        if mirror_data:
            apply_mirror_data(mirror_data)

    def _prepare_flip(self, source_node, dest_node):
        """
        Return settings gathered in preparation for flipping two nodes.
        """
        source_to_dest_data = get_mirror_data(source_node, dest_node, self.params)
        dest_to_source_data = get_mirror_data(dest_node, source_node, self.params)
        return source_to_dest_data, dest_to_source_data

    def _apply_flip(self, flip_data):
        """
        Apply the flip data gathered from `_prepare_flip,` which will
        move the nodes to their flipped locations.
        """
        source_to_dest_data, dest_to_source_data = flip_data
        if source_to_dest_data and dest_to_source_data:
            apply_mirror_data(source_to_dest_data)
            apply_mirror_data(dest_to_source_data)

    def flip(self, source_node, dest_node):
        """
        Flip the transforms of two nodes such that each
        node moves to the mirrored transform of the other.
        """
        flip_data = self._prepare_flip(source_node, dest_node)
        self._apply_flip(flip_data)

    def flip_multiple(self, node_pairs: List[Tuple[pm.nt.Transform, pm.nt.Transform]]):
        """
        Perform `flip` on multiple nodes, by gathering first and then applying second,
        in order to avoid parenting and dependency issues.

        Args:
            node_pairs: A list of (source, dest) node pairs to flip.
        """
        flip_data_list = []
        for (source_node, dest_node) in node_pairs:
            flip_data = self._prepare_flip(source_node, dest_node)
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
        all_mirror_data = []

        for node in nodes:
            params = copy(self.params)
            params.mirror_mode = MirrorMode.ALIGNED
            mirror_data = get_mirror_data(node, node, params)
            all_mirror_data.append(mirror_data)

        # TODO: attempt to automatically handle parent/child relationships
        #       to lift the requirement of giving nodes in hierarchical order
        for mirror_data in all_mirror_data:
            apply_mirror_data(mirror_data)


class MirrorCurveShapes(MirrorOperation):
    """
    Mirrors the NurbsCurve shapes of a node by simply
    flipping them, assuming MirrorTransformations would also
    be run on the mirrored nodes.
    """

    def __init__(self):
        super(MirrorCurveShapes, self).__init__()

        self.mirrorMode = MirrorMode.SIMPLE

        # delete and replace curve shapes when mirroring
        self.replaceExistingShapes = True

        # the shape types to consider when replacing existing shapes
        self.shapeTypes = ["nurbsCurve"]

    @overrides
    def mirror_node(self, source_node: pm.nt.Transform, dest_node: pm.nt.Transform, is_new_node: bool):
        # curve shape mirroring doesn't care about the actual
        # position, its only job is to flip the curve
        if is_new_node:
            MirrorCurveShapes.flip_all_curve_shapes(dest_node, self.axis, self.mirrorMode)
        elif self.replaceExistingShapes:
            self.replace_curve_shapes(source_node, dest_node)
            MirrorCurveShapes.flip_all_curve_shapes(dest_node, self.axis, self.mirrorMode)

    @staticmethod
    def flip_all_curve_shapes(node, axis=0, mirrorMode=MirrorMode.SIMPLE):
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
    def flip_curve_shape(curve_shape, axis=0, mirrorMode=MirrorMode.SIMPLE):
        """
        Flip the position of all cvs in a curve shape in a manner that
        corresponds to the transformation mirror modes.

        Args:
            curve_shape (NurbsCurve): The curve to mirror
            axis (int): An axis to mirror across
            mirrorMode: The MirrorMode type to use
        """
        if mirrorMode == MirrorMode.SIMPLE:
            pm.scale(curve_shape.cv, [-1, -1, -1])
        elif mirrorMode == MirrorMode.ALIGNED:
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

    @overrides
    def mirror_node(self, source_node: pm.nt.Transform, dest_node: pm.nt.Transform, is_new_node: bool):
        if source_node.type() == "joint" and dest_node.type() == "joint":
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
    regex = re.compile(f"(?<![^_]){search}(?=(_|$))")
    return regex, replace


def _generate_mirror_name_replacements(config):
    """
    Generate and return the full list of replacement pairs.

    Returns:
        A list of (regex, replacement) tuples.
    """
    replacements = []
    sym_config = config.get("symmetry", {})
    pairs = sym_config.get("pairs", [])

    for pair in pairs:
        if "left" in pair and "right" in pair:
            left = pair["left"]
            right = pair["right"]
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

    @overrides
    def mirror_node(self, source_node: pm.nt.Transform, dest_node: pm.nt.Transform, is_new_node: bool):
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

    @overrides
    def mirror_node(self, source_node: pm.nt.Transform, dest_node: pm.nt.Transform, is_new_node: bool):
        source_color = nodes.get_override_color(source_node)
        if source_color:
            # get name of source color
            source_name = editor_utils.get_color_name(source_color)
            if source_name:
                # mirror the name
                dest_name = _get_mirrored_name_with_replacements(source_name, self._get_replacements())
                # get color of mirrored name
                dest_color = editor_utils.get_named_color(dest_name)
                if dest_color:
                    nodes.set_override_color(dest_node, tuple(dest_color))


class MirrorLinks(BlueprintMirrorOperation):
    """
    Mirrors Blueprint links. See links.py
    """

    @overrides
    def mirror_node(self, source_node: pm.nt.Transform, dest_node: pm.nt.Transform, is_new_node: bool):
        # get link meta data
        source_link_data = links.get_link_meta_data(source_node)
        dest_link_data = links.get_link_meta_data(dest_node)

        if source_link_data:
            # if no destination link data already exists, create
            # a copy of the source link data, otherwise only affect the target node
            if not dest_link_data:
                dest_link_data = source_link_data

            # TODO: provide a layer of abstraction, mirroring shouldn't have to know the details

            source_target_nodes = source_link_data.get("targetNodes")
            if source_target_nodes:
                dest_target_nodes = [get_paired_node(n) for n in source_target_nodes]
                if dest_target_nodes:
                    dest_link_data["targetNodes"] = dest_target_nodes
                    links.set_link_meta_data(dest_node, dest_link_data)

            # position the dest node using the link
            links.apply_link_position(dest_node)

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
                children = nodes.get_descendants_top_to_bottom(sourceNode, type=["transform", "joint"])

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

        for source_node in source_nodes:
            if self.validateNodes:
                validate_mirror_node(source_node)

            if self.isCreationAllowed:
                dest_node, is_new_node = self._get_or_create_pair_node(source_node)
                if dest_node and is_new_node:
                    self._newNodes.append(dest_node)
            else:
                dest_node = get_paired_node(source_node)

            if dest_node:
                pairs.append((source_node, dest_node))
            else:
                LOG.warning("Could not get pair node for: %s", source_node)

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


class MirrorParams(object):
    """
    Parameters that define how mirroring should be performed.
    """

    def __init__(self):
        self.mirror_mode = MirrorMode.SIMPLE
        self.axis = 0
        self.axis_mtx = None

        self.mirror_translate = True
        self.mirror_rotate = True
        self.mirror_rotate_order = True

        self.affect_translate = True
        self.affect_rotate = True
        self.affect_scale = True
        self.affect_attrs = True

        # list of custom attribute names to copy without changing value
        self.mirrored_attr_names = []
        # dict of custom attribute names to mirroring expressions to apply
        self.custom_mirror_attr_exps = {}


class MirrorData(object):
    """
    Data that represents mirrored matrices and attributes for a node.
    """

    def __init__(self, source_node, dest_node, params: MirrorParams):
        # the params that determine how to perform mirroring
        self.params = params
        # the source node of the mirror
        self.source_node = source_node
        # the node to receive the mirrored data
        self.dest_node = dest_node
        # the mirrored matrices to apply
        self.matrices = []
        # the mirrored attribute values to apply
        self.attrs = {}

    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.dest_node})>"


def get_mirror_data(
    source_node: pm.nt.Transform, dest_node: pm.nt.Transform = None, params: MirrorParams = None
) -> Optional[MirrorData]:
    """
    Return a MirrorData object that represents mirroring to apply from a source node to a target node.

    Args:
        source_node: The source node of the mirroring.
        dest_node: The destination node that would be updated to match the source node.
        params: The parameters controlling how to perform mirroring.

    Returns:
        A MirrorData object.
    """
    if params is None:
        params = MirrorParams()

    if not dest_node:
        dest_node = get_paired_node(source_node)

    if not dest_node:
        # could not find a destination node
        return

    # copy params to ensure they don't change later
    out_params = copy(params)

    result = MirrorData(source_node, dest_node, out_params)
    result.matrices = get_mirrored_matrices(source_node, params=out_params)

    # gather mirrored attributes from custom expressions
    for attr_name, expression in params.custom_mirror_attr_exps.items():
        if not expression:
            continue
        source_val = result.attrs.get(attr_name)
        mirrored_val = eval_custom_mirror_attr_exp(source_node, dest_node, attr_name, expression)
        result.attrs[attr_name] = mirrored_val
        LOG.debug(
            "Mirrored custom attribute %s: %s -> %s, expression:\n%s", attr_name, source_val, mirrored_val, expression
        )

    # then gather any simple custom attributes to mirror without changing the value
    for attr_name in params.mirrored_attr_names:
        if attr_name not in result.attrs:
            attr_value = getattr(source_node, attr_name).get()
            result.attrs[attr_name] = attr_value

    return result


def apply_mirror_data(mirror_data: MirrorData):
    """
    Apply MirrorData matrices or attribute values to it's destination node.
    """
    LOG.debug("Applying Mirror Settings: %s", mirror_data)
    params = mirror_data.params
    if any([params.affect_translate, params.affect_rotate, params.affect_scale]):
        set_mirrored_matrices(
            mirror_data.dest_node,
            mirror_data.matrices,
            translate=params.affect_translate,
            rotate=params.affect_rotate,
            scale=params.affect_scale,
        )

    if params.affect_attrs:
        for attr_name, val in mirror_data.attrs.items():
            LOG.debug("%s -> %s", attr_name, val)
            attr = mirror_data["destNode"].attr(attr_name)
            attr.set(val)


def eval_custom_mirror_attr_exp(source_node, dest_node, attr, exp):
    LOG.debug("Raw Exp: %s", repr(exp))

    _globals = {"node": source_node, "dest_node": dest_node}

    if hasattr(source_node, attr):
        _globals["value"] = getattr(source_node, attr).get()
    else:
        raise KeyError(f"{source_node} missing mirrored attr {attr}")
    if hasattr(dest_node, attr):
        _globals["dest_value"] = getattr(dest_node, attr).get()
    else:
        raise KeyError(f"{dest_node} missing mirrored attr {attr}")

    # Add a return to the last line of the expression, so we can treat it as a function
    body = [line for line in exp.strip().split("\n") if line]
    last_line = body.pop(-1)
    _exp = CUSTOM_EXP_FMT.format(body="\n\t".join(body + [""]), lastLine=last_line)

    # TODO: do this without exec
    exec(_exp, _globals)
    result = _globals["result"]

    return result


def get_mirrored_matrices(node, params: MirrorParams) -> dict:
    """
    Return the mirrored matrix or matrices for the given node
    Automatically handles Transform vs. Joint differences

    Args:
        node: The node whose matrices should be mirrored.
        params: The params defining how to mirror the node.

    Returns:
        A dict with a 'type' key ('node' or 'joint'), and the corresponding mirrored matrices.
    """
    result = {}
    if isinstance(node, pm.nt.Joint):
        result["type"] = "joint"
        jnt_matrices = joints.get_joint_matrices(node)
        result["matrices"] = get_mirrored_joint_matrices(*jnt_matrices, params=params)
    else:
        node_wm = nodes.get_world_matrix(node)
        result["type"] = "node"
        result["matrices"] = [get_mirrored_transform_matrix(node_wm, params=params)]
    return result


def set_mirrored_matrices(node, mirrored_matrices, translate=True, rotate=True, scale=True):
    """
    Set the world matrix for the given node using the given mirrored matrices
    Automatically interprets Transform vs. Joint matrix settings
    """
    if mirrored_matrices["type"] == "joint":
        LOG.debug("Applying Joint Matrices")
        joints.set_joint_matrices(node, *mirrored_matrices["matrices"], translate=translate, rotate=rotate)
    else:
        LOG.debug("Applying Transform Matrix")
        nodes.set_world_matrix(node, *mirrored_matrices["matrices"], translate=translate, rotate=rotate, scale=scale)


def get_mirrored_transform_matrix(matrix, params: MirrorParams):
    """
    Return the mirrored version of the given matrix.

    Args:
        matrix: The matrix to mirror.
        params: The parameters that define how to mirror the matrix.
    """
    axis = nodes.get_axis(params.axis)

    axis_mtx = params.axis_mtx
    if params.axis_mtx is not None:
        # remove scale from the axisMatrix
        axis_mtx = nodes.get_scale_matrix(params.axis_mtx).inverse() * params.axis_mtx
        matrix = matrix * axis_mtx.inverse()

    s = nodes.get_scale_matrix(matrix)
    r = nodes.get_rotation_matrix(matrix)
    t = matrix[3]

    if params.mirror_translate:
        # negate translate vector
        t[axis.index] = -t[axis.index]

    if params.mirror_rotate:
        r = invert_other_axes(r, axis)
        if params.mirror_mode == MirrorMode.ALIGNED:
            LOG.debug("Counter Rotating because mirror mode is ALIGNED")
            r = counter_rotate_for_non_mirrored(r, axis)

    mirror = s * r
    mirror[3] = t

    if axis_mtx is not None:
        mirror = mirror * axis_mtx

    return mirror


def get_mirrored_joint_matrices(matrix, r, ra, jo, params: MirrorParams) -> list:
    """
    Return the given joint matrices mirrored across the given axis.
    Returns the full transformation matrix, rotation, rotation axis,
    and joint orient matrices.

    Args:
        params: The parameters that define how to mirror the matrices.
    """
    LOG.debug("Getting Mirrored Joint Matrices")

    axis_mtx = params.axis_mtx

    # matches transform orientation
    mirror = get_mirrored_transform_matrix(matrix, params)
    if params.mirror_rotate:

        if axis_mtx is not None:
            # matches orientation with jo
            inv_scale_mtx = nodes.get_scale_matrix(params.axis_mtx).inverse()
            axis_mtx = inv_scale_mtx * params.axis_mtx
            jo = jo * axis_mtx.inverse()

        # flips orientation
        jo = invert_other_axes(jo, params.axis)
        if params.mirror_mode == MirrorMode.ALIGNED:
            LOG.debug("Counter Rotating because mirror mode is ALIGNED")
            # changes orientation to inverted world
            jo = counter_rotate_for_mirrored_joint(jo)

        if axis_mtx is not None:
            # TODO (bsayre): doesn't seem to do anything...
            jo = jo * axis_mtx

    return [mirror, r, ra, jo]


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


class MirrorActionUtil(object):
    """
    A util class for mirroring BuildAction data.
    """

    def __init__(self, config: dict):
        self.config = config

    def mirror_action(self, src_action: BuildActionProxy, dst_action: BuildActionProxy):
        """
        Mirror a BuildActionProxy. Does not handle syncing other settings, so the actions are expected
        to be identical before being mirrored.
        """
        if not dst_action or dst_action.action_id != src_action.action_id:
            # action was set up incorrectly
            LOG.warning("Cannot mirror %s -> %s, destination action is not the same type", src_action, dst_action)
            return False

        #  mirror invariant attr values
        for _, src_attr in src_action.get_attrs().items():
            if not src_action.is_variant_attr(src_attr.name):
                dst_attr = dst_action.get_attr(src_attr.name)
                value = src_attr.get_value()
                mirrored_value = self._mirror_action_value(src_attr, value)
                if mirrored_value != value:
                    dst_attr.set_value(mirrored_value)
                    LOG.debug("%s -> %s", value, mirrored_value)

        # mirror variant attr values
        for i, src_variant in enumerate(src_action.get_variants()):
            dst_variant = dst_action.get_variant(i)
            for _, src_attr in src_variant.get_attrs().items():
                dst_attr = dst_variant.get_attr(src_attr.name)
                value = src_attr.get_value()
                mirrored_value = self._mirror_action_value(src_attr, value)
                if mirrored_value != value:
                    dst_attr.set_value(mirrored_value)
                    LOG.debug("[%d] %s -> %s", i, value, mirrored_value)

        return True

    def _mirror_action_value(self, attr: BuildActionAttribute, value):
        """
        Return a mirrored value of an attribute, taking into account attribute types and config.

        Args:
            attr: BuildActionAttribute
                The attribute to mirror.
            value:
                The attribute value to mirror.
        """
        if not attr.config.get("canMirror", True):
            # don't mirror the attributes value, just copy it
            return value

        def _get_paired_node_or_self(node):
            """
            Return the paired node of a node, if one exists, otherwise return the node.
            """
            paired_node = get_paired_node(node)
            if paired_node:
                return paired_node
            return node

        if not value:
            return value

        # TODO: move mirror logic into BuildActionAttribute and type-specific subclasses?

        if attr.type == BuildActionAttributeType.NODE:
            return _get_paired_node_or_self(value)

        elif attr.type == BuildActionAttributeType.NODE_LIST:
            return [_get_paired_node_or_self(node) for node in value]

        elif attr.type == BuildActionAttributeType.STRING:
            return get_mirrored_name(value, self.config)

        elif attr.type == BuildActionAttributeType.STRING_LIST:
            return [get_mirrored_name(v, self.config) for v in value]

        return value
