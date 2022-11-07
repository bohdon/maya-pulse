import logging
from enum import IntEnum
from typing import Optional

import maya.cmds as cmds
import pymel.core as pm

from pulse.colors import LinearColor

LOG = logging.getLogger(__name__)

IDENTITY_MATRIX_FLAT = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


class ConnectMatrixMethod(IntEnum):
    """
    Options for connecting a matrix to a nodes offsetParentMatrix attribute
    """

    # only connect the offset parent matrix, keep all other attributes the same
    CONNECT_ONLY = 0
    # zero out all relative transform values once connected
    SNAP = 1
    # restore the previous world position once connected, modifying relative transform values if necessary
    KEEP_WORLD = 2
    # create an offset to preserve the current world position, as well as the current relative transform values
    CREATE_OFFSET = 3


# Node Retrieval
# --------------


def get_all_parents(node, include_node=False):
    """
    Return all parents of a node

    Args:
        node: A node to find parents for.
        include_node: A bool, whether to include the given node in the result.

    Returns:
        A list of nodes
    """
    if isinstance(node, str):
        split = node.split("|")
        return ["|".join(split[:i]) for i in reversed(range(2, len(split)))]
    parents = []
    parent = node.getParent()
    if parent is not None:
        parents.append(parent)
        parents.extend(get_all_parents(parent))
    if include_node:
        parents.insert(0, node)
    return parents


def get_parent_nodes(nodes):
    """
    Returns the top-most parent nodes of all nodes
    in a list.

    Args:
        nodes: A list of nodes
    """
    # TODO: optimize using long names and string matching
    result = []
    for n in nodes:
        if any([p in nodes for p in get_all_parents(n)]):
            continue
        result.append(n)
    return result


def get_node_branch(root, end):
    """
    Return all nodes in a transform hierarchy branch starting
    from root and descending to end.

    Returns None if the end node is not child of root.

    Args:
        root (PyNode): The top node of a branch
        end (PyNode): The end node of a branch, must be a child of root
    """
    if not end.isChildOf(root):
        return
    nodes = get_all_parents(end)
    nodes.reverse()
    nodes.append(end)
    index = nodes.index(root)
    return nodes[index:]


def duplicate_branch(root, end, parent=None, name_fmt="{0}"):
    """
    Duplicate a node branch from root to end (inclusive).

    Args:
        root (PyNode): The root node of the branch.
        end (PyNode): The end node of the branch.
        parent (PyNode): The parent node of the new node branch.
        name_fmt (str): The naming format to use for the new nodes.
            Will be formatted with the name of the original nodes.
    """
    result = []
    all_nodes = get_node_branch(root, end)
    if all_nodes is None:
        raise ValueError(f"Invalid root and end nodes: {root} {end}")
    next_parent = parent
    for node in all_nodes:
        # duplicate only this node
        new_node = pm.duplicate(node, parentOnly=True)[0]
        new_node.rename(name_fmt.format(node.nodeName()))
        new_node.setParent(next_parent)
        # use this node as parent for the next
        next_parent = new_node
        result.append(new_node)
    return result


def get_assemblies(nodes):
    """
    Return any top-level nodes (assemblies) that
    contain a list of nodes

    Args:
        nodes: A list of node long-names. Does not support
            short names or PyNodes.
    """
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]
    return list(set([n[: (n + "|").find("|", 1)] for n in nodes]))


# Transform Parenting
# -------------------


def get_descendants_top_to_bottom(node, **kwargs):
    """
    Return a list of all the descendants of a node,
    in hierarchical order, from top to bottom.

    Args:
        node (PyNode): A dag node with children
        **kwargs: Kwargs given to the listRelatives command
    """
    return reversed(node.listRelatives(ad=True, **kwargs))


def get_transform_hierarchy(transform, include_parent=True):
    """
    Return a list of (parent, [children]) tuples for a transform
    and all of its descendants.

    Args:
        transform: A Transform node.
        include_parent: A bool, when True, the relationship between
            the transform and its parent is included.
    """
    result = []
    if include_parent:
        result.append((transform.getParent(), [transform]))

    descendants = transform.listRelatives(ad=True, type="transform")

    for t in [transform] + descendants:
        children = t.getChildren(type="transform")
        if children:
            result.append((t, children))

    return result


def set_transform_hierarchy(hierarchy):
    """
    Re-parent one or more transform nodes.

    Args:
        hierarchy: A list of (parent, [children]) tuples
    """

    for (parent, children) in hierarchy:
        set_parent(children, parent)


def set_parent(children, parent):
    """
    Parent one or more nodes to a new parent node.
    Resolves situations where a node is currently a
    parent of its new parent.

    Args:
        children: A list of nodes to reparent
        parent: A node to use as the new parent
    """
    if not isinstance(children, (list, tuple)):
        children = [children]
    # eliminate nodes that are already correctly children
    children = [c for c in children if c.getParent() != parent]
    if not children:
        # nothing left to do
        return
    # find any issues where a child is a current parent of the new parent
    if parent is not None:
        conflicts = []
        for child in children:
            if parent.hasParent(child):
                conflicts.append(child)
        if conflicts:
            # move the parent node so that it
            # becomes a sibling of a top-most child node
            tops = get_parent_nodes(conflicts)
            pm.parent(parent, tops[0].getParent())
    args = children[:] + [parent]
    pm.parent(*args)


def parent_in_order(nodes):
    """
    Parent the given nodes to each other in order.
    Leaders then followers, eg. [A, B, C] -> A|B|C

    Args:
        nodes: A list of nodes to parent to each other in order
    """
    if len(nodes) < 2:
        LOG.warning("More than one node must be given")
        return
    # find the first parent of our new parent that is not
    # going to be a child in the new hierarchy, this prevents
    # nodes from being improperly pushed out of the hierarchy
    # when setParent resolves child->parent issues
    safe_parent = nodes[0].getParent()
    while safe_parent in nodes:
        safe_parent = safe_parent.getParent()
        if safe_parent is None:
            # None should never be in the given list of nodes,
            # but this is a failsafe to prevent infinite loop if it is
            break
    set_parent(nodes, safe_parent)
    # parent all nodes in order
    for i in range(len(nodes) - 1):
        parent, child = nodes[i : i + 2]
        set_parent(child, parent)


# Node Creation
# -------------


def create_offset_transform(node, name="{0}_offset"):
    """
    Create a transform that is inserted as the new parent of a node,
    at the same world location as the node. This effectively transfers
    the local matrix of a node into the new transform, zeroing out
    the attributes of the node (usually for animation). This includes
    absorbing the rotate-axis of the node.

    Args:
        node (PyNode): A node to create an offset for
        name (str): The name to use for the new transform. Accepts a single
            format argument which will be the name of `node`
    """
    # create the offset transform
    _name = name.format(node.nodeName())
    offset = pm.createNode("transform", n=_name)

    # parent the offset to the node and reset
    # its local transformation
    offset.setParent(node)
    pm.xform(
        offset,
        objectSpace=True,
        translation=[0, 0, 0],
        rotation=[0, 0, 0],
        scale=[1, 1, 1],
        shear=[0, 0, 0],
    )

    # with transforms now absorbed, move offset to be a sibling of the node
    offset.setParent(node.getParent())

    # now parent the node to the new offset, and reset its transform
    node.setParent(offset)
    pm.xform(
        node,
        objectSpace=True,
        translation=[0, 0, 0],
        rotation=[0, 0, 0],
        scale=[1, 1, 1],
        shear=[0, 0, 0],
        # reset rotate axis since it is now part
        # of the offset transform
        rotateAxis=[0, 0, 0],
    )
    if cmds.about(api=True) >= 20200000:
        # also need to reset offsetParentMatrix
        node.opm.set(pm.dt.Matrix())

    return offset


# Attribute Retrieval
# -------------------


def get_expanded_attr_names(attrs):
    """
    Given a list of compound attribute names, return a
    list of all leaf attributes that they represent.
    Only supports the more common transform attributes.

    e.g. ['t', 'rx', 'ry'] -> ['tx', 'ty', 'tz', 'rx', 'ry']

    Args:
        attrs (list of str): The attributes to expand
    """
    _attrs = []
    for attr in attrs:
        if attr in ("t", "r", "rp", "s", "sp", "ra"):
            # translate, rotate, scale and their pivots, also rotate axis
            _attrs.extend([attr + a for a in "xyz"])
        elif attr in ("sh",):
            # shear
            _attrs.extend([attr + a for a in ("xy", "xz", "yz")])
        else:
            # not a known compound attribute
            _attrs.append(attr)
    return _attrs


def safe_get_attr(node, attr_name):
    """
    Return an attribute from a node by name.
    Returns None if the attribute does not exist.

    Args:
        node (PyNode): The node with the attribute.
        attr_name (str): The attribute name.
    """
    if node.hasAttr(attr_name):
        return node.attr(attr_name)


def get_compound_attr_index(child_attr):
    """
    Return the index of the given compound child attribute.

    Args:
        child_attr (Attribute): An attribute that is the child of a compound attr.
    """
    if not child_attr.isChild():
        raise ValueError(f"Attribute is not a child of a compound attribute: {child_attr}")
    return child_attr.getParent().getChildren().index(child_attr)


def get_attr_dimension(attr):
    """
    Return the dimension of an Attribute

    Args:
        attr (Attribute): The attribute to check
    """
    if attr.isCompound():
        return attr.numChildren()
    else:
        return 1


def get_attr_or_value_dimension(attr_or_value):
    """
    Return the dimension of an attribute or
    attribute value (such as a list or tuple)

    Args:
        attr_or_value: An Attribute or value that can be set on an attribute
    """
    if isinstance(attr_or_value, pm.Attribute):
        return get_attr_dimension(attr_or_value)
    elif isinstance(attr_or_value, pm.dt.Matrix):
        # matrices need to be treated as single dimension, since
        # matrix attributes are singular
        return 1
    else:
        # support duck-typed lists
        if not isinstance(attr_or_value, str):
            try:
                return len(attr_or_value)
            except:
                pass
    return 1


# Constraints
# -----------


def set_constraint_locked(constraint, locked):
    """
    Lock all important attributes on a constraint node

    Args:
        constraint: A ParentConstraint or ScaleConstraint node
        locked: A bool, whether to make the constraint locked or unlocked
    """
    attrs = ["nodeState"]
    if isinstance(constraint, pm.nt.ScaleConstraint):
        attrs.extend(["offset%s" % a for a in "XYZ"])
    elif isinstance(constraint, pm.nt.ParentConstraint):
        targets = constraint.target.getArrayIndices()
        for i in targets:
            attrs.extend(["target[%d].targetOffsetTranslate%s" % (i, a) for a in "XYZ"])
            attrs.extend(["target[%d].targetOffsetRotate%s" % (i, a) for a in "XYZ"])
    for a in attrs:
        constraint.attr(a).setLocked(locked)


def convert_scale_constraint_to_world_space(scale_constraint):
    """
    Modify a scale constraint to make it operate better with
    misaligned axes between the leader and follower by plugging
    the worldMatrix of the leader node into the scale constraint.

    Args:
        scale_constraint: A ScaleConstraint node
    """
    for i in range(scale_constraint.target.numElements()):
        inputs = scale_constraint.target[i].targetParentMatrix.inputs(p=True)
        for input in inputs:
            if input.longName().startswith("parentMatrix"):
                # disconnect and replace with world matrix
                input // scale_constraint.target[i].targetParentMatrix
                input.node().wm >> scale_constraint.target[i].targetParentMatrix
                # also disconnect target scale
                scale_constraint.target[i].targetScale.disconnect()
                break


def full_constraint(leader, follower):
    """
    Fully constrain a follower node to a leader node.
    Does this by creating a parent and scale constraint.

    Args:
        leader (PyNode or str): The leader node of the constraint
        follower (PyNode or str): The follower node of the constraint

    Returns:
        A parentConstraint and a scaleConstraint node
    """
    pc = pm.parentConstraint(leader, follower)
    sc = pm.scaleConstraint(leader, follower)
    # hiding the constraints prevents camera framing
    # issues in certain circumstances
    pc.visibility.set(0)
    sc.visibility.set(0)
    return pc, sc


def connect_matrix(
    matrix: pm.Attribute,
    node: pm.nt.Transform,
    method: ConnectMatrixMethod = ConnectMatrixMethod.KEEP_WORLD,
    keep_joint_hierarchy=True,
):
    """
    Connect a world matrix to a node, optionally preserving or changing transform
    attributes to adjust accordingly (see `ConnectMatrixMethod`).

    Uses either the offsetParentMatrix, or decomposes and connects via transform attributes.

    When using offsetParentMatrix, inheritsTransform will be disabled to keep the connection simple.


    Args:
        matrix: A matrix attribute
        node: A transform node
        method: The method to use for adjusting the node's transform after connecting
        keep_joint_hierarchy: When true, joints are handled specially, and instead of connecting to the
            offsetParentMatrix and disabling inheritsTransform, a joint matrix constrain is used.
            This is necessary if joint animation baking and export will be used.
    """
    # TODO: allow the user to specify whether they want to decompose or use offsetParentMatrix (while also
    #       providing special case joint handling). Use ConnectMatrixMethod for this, and rename the current
    #       ConnectMatrixMethod to something like ConnectMatrixAdjustMethod

    if method == ConnectMatrixMethod.CONNECT_ONLY:
        # make the connection
        _make_matrix_connection(matrix, node, keep_joint_hierarchy)

    elif method == ConnectMatrixMethod.SNAP:
        # make the connection
        _make_matrix_connection(matrix, node, keep_joint_hierarchy)
        # TODO: also zero out rotate axis?
        # TODO: unlock/re-lock ra and jo when doing this
        # zero out joint orients
        if node.hasAttr("jointOrient"):
            node.jointOrient.set((0, 0, 0))
        # zero out transform values
        cmds.xform(node.longName(), matrix=IDENTITY_MATRIX_FLAT, worldSpace=False)

    elif method == ConnectMatrixMethod.KEEP_WORLD:
        if keep_joint_hierarchy and node.nodeType() == "joint":
            raise ValueError(
                "ConnectMatrixMethod.KEEP_WORLD is not supported with joints and keep_joint_hierarchy=True, "
                "use CREATE_OFFSET instead"
            )

        # remember the node's world matrix
        world_mtx = node.wm.get()
        # make the connection
        matrix >> node.offsetParentMatrix
        node.inheritsTransform.set(False)
        # restore the world matrix
        set_world_matrix(node, world_mtx)

    elif method == ConnectMatrixMethod.CREATE_OFFSET:
        # calculate and store offset using a multMatrix node
        offset_mtx = node.pm.get() * matrix.get().inverse()
        mult_mtx = pm.createNode("multMatrix", n=f"{node.nodeName()}_mtxcon_offset_multMatrix")
        mult_mtx.matrixIn[0].set(offset_mtx)
        matrix >> mult_mtx.matrixIn[1]
        # make the connection
        _make_matrix_connection(mult_mtx.matrixSum, node, keep_joint_hierarchy)


def _make_matrix_connection(matrix: pm.Attribute, node: pm.nt.Transform, keep_joint_hierarchy=True):
    """
    Perform the actual matrix connection of a node, either connecting offsetParentMatrix or decomposing
    if the node is a joint and `keep_joint_hierarchy` is True. See `connect_matrix`
    """
    if keep_joint_hierarchy and node.nodeType() == "joint":
        decompose_and_connect_matrix(matrix, node, inherits_transform=True)
    else:
        matrix >> node.offsetParentMatrix
        node.inheritsTransform.set(False)


def decompose_and_connect_matrix(matrix: pm.Attribute, node: pm.nt.Transform, inherits_transform: bool = False):
    """
    Decompose a matrix and connect it to the translate, rotate, scale, and shear of a transform node.

    Args:
        matrix: A world space matrix attribute
        node: A transform node
        inherits_transform: If true, add a `multMatrix` node to compute the local matrix before decomposing,
            If false, disable inheritsTransform on the node and connect the world space matrix directly.

    Returns:
        The `decomposeMatrix` node
    """
    from pulse import util_nodes

    if inherits_transform:
        # get local space matrix, and ensure inheritsTransform is enabled
        mtx = util_nodes.mult_matrix(matrix, node.pim)
        mtx.node().rename(f"{node.nodeName()}_worldToLocal_multMatrix")
        node.inheritsTransform.set(True)
    else:
        # decompose world space matrix directly, so any parent transformations must be removed
        mtx = matrix
        node.inheritsTransform.set(False)

    decomp = util_nodes.decompose_matrix(mtx)
    node.rotateOrder >> decomp.inputRotateOrder
    decomp.outputTranslate >> node.translate
    decomp.outputRotate >> node.rotate
    decomp.outputScale >> node.scale
    decomp.outputShear >> node.shear

    node.translate.setLocked(True)
    node.rotate.setLocked(True)
    node.scale.setLocked(True)
    node.shear.setLocked(True)

    # TODO: handle locked attrs

    if not node.rotateAxis.isLocked():
        node.rotateAxis.set((0, 0, 0))

    if node.hasAttr("jointOrient") and not node.jointOrient.isLocked():
        node.jointOrient.set((0, 0, 0))

    return decomp


def disconnect_offset_matrix(
    follower, preserve_position=True, preserve_transform_values=True, keep_inherit_transform=False
):
    """
    Disconnect any inputs to the offsetParentMatrix of a node, and re-enable inheritsTransform.

    Args:
        follower (PyNode): A node with input connections to offsetParentMatrix
        preserve_position (bool): If true, preserve the followers world space position
        preserve_transform_values (bool): If true, preserve_position will not affect the
            current translate, rotate, and scale values of the follower by absorbing
            any offset into the follower's offsetParentMatrix.
        keep_inherit_transform (bool): If true, inheritsTransform will not be changed
    """
    if not preserve_position:
        follower.opm.disconnect()
        if not keep_inherit_transform:
            follower.inheritsTransform.set(True)
    else:
        # remember world matrix
        wm = get_world_matrix(follower)

        # enable inherit transform so that its as if previously
        # replaced parent matrix contributors are restored
        if not keep_inherit_transform:
            follower.inheritsTransform.set(True)

        follower.opm.disconnect()

        if preserve_transform_values:
            # m needs to stay the same, opm will be set to the delta between the new parent matrix
            # (parent node's world matrix, without this node's opm) and the old follower world matrix.
            pm_without_opm = follower.opm.get().inverse() * follower.pm.get()
            delta_to_old_om = follower.im.get() * wm * pm_without_opm.inverse()
            follower.opm.set(delta_to_old_om)
        else:
            # zero out opm and restore world matrix
            follower.opm.set(pm.dt.Matrix())
            set_world_matrix(follower, wm)


# Transform Modification
# ----------------------


def freeze_scales_for_hierarchy(node: pm.nt.DagNode):
    """
    Freeze scales on a transform and all its descendants without affecting pivots.
    Does this by parenting all children to the world, freezing, then restoring the hierarchy.

    Args:
        node (pm.PyNode): A Transform node
    """
    hierarchy = get_transform_hierarchy(node)
    children = node.listRelatives(ad=True, type="transform")
    for c in children:
        c.setParent(None)
    for n in [node] + children:
        pm.makeIdentity(n, t=False, r=False, s=True, n=False, apply=True)
    set_transform_hierarchy(hierarchy)


def freeze_pivot(transform):
    """
    Freeze the given transform such that its local pivot becomes zero,
    but its world space pivot remains unchanged.

    Args:
        transform: A Transform node
    """
    pivot = pm.dt.Vector(pm.xform(transform, q=True, rp=True, worldSpace=True))
    # asking for world space translate gives different result than world space matrix
    # translate. we want the former in this situation because we will be setting
    # with the same world space translate method
    translate = pm.dt.Vector(pm.xform(transform, q=True, t=True, worldSpace=True))
    parent_translate = pm.dt.Vector()
    parent = transform.getParent()
    if parent:
        # we want the world space matrix translate of the parent
        # because that's the real location that zeroed out child transforms would exist.
        # note that the world space translate (not retrieving matrix) can be a different value
        parent_translate = pm.dt.Matrix(pm.xform(parent, q=True, m=True, worldSpace=True)).translate
    # move current pivot to the parents world space location
    pm.xform(transform, t=(translate - pivot + parent_translate), ws=True)
    # now that the transform is at the same world space position as its parent, freeze it
    pm.makeIdentity(transform, t=True, apply=True)
    # restore world pivot position with translation
    pm.xform(transform, t=pivot, ws=True)


def freeze_pivots_for_hierarchy(transform):
    """
    Freeze pivots on a transform and all its descendants.

    Args:
        transform: A Transform node
    """
    hierarchy = get_transform_hierarchy(transform)
    children = transform.listRelatives(ad=True, type="transform")
    for c in children:
        c.setParent(None)
    for n in [transform] + children:
        freeze_pivot(n)
    set_transform_hierarchy(hierarchy)


def freeze_offset_matrix(transform):
    """
    Freeze the translate, rotate, and scale of a transform by moving its
    current local matrix values into its offsetParentMatrix. This operation is idempotent.
    """
    if not transform.offsetParentMatrix.isSettable():
        LOG.warning("Cannot freeze %s offset matrix, offsetParentMatrix is not settable", transform)
        return
    local_mtx = transform.m.get()
    offset_mtx = transform.offsetParentMatrix.get()
    new_offset_mtx = local_mtx * offset_mtx
    transform.offsetParentMatrix.set(new_offset_mtx)
    transform.setMatrix(pm.dt.Matrix())


def freeze_offset_matrix_for_hierarchy(transform):
    children = transform.listRelatives(ad=True, type="transform")
    for node in [transform] + children:
        freeze_offset_matrix(node)


def unfreeze_offset_matrix(transform):
    """
    Unfreeze the translate, rotate, and scale of a transform by moving its current
    offset parent matrix values into its translate, rotate, and scale. This operation is idempotent.
    """
    if not transform.offsetParentMatrix.isSettable():
        LOG.warning("Cannot unfreeze %s offset matrix, offsetParentMatrix is not settable", transform)
        return
    local_mtx = transform.m.get()
    offset_mtx = transform.offsetParentMatrix.get()
    new_local_mtx = local_mtx * offset_mtx
    transform.setMatrix(new_local_mtx)
    transform.offsetParentMatrix.set(pm.dt.Matrix())


def unfreeze_offset_matrix_for_hierarchy(transform):
    children = transform.listRelatives(ad=True, type="transform")
    for node in [transform] + children:
        unfreeze_offset_matrix(node)


def get_euler_rotation_from_matrix(matrix):
    """
    Return the euler rotation in degrees of a matrix
    """
    if not isinstance(matrix, pm.dt.TransformationMatrix):
        matrix = pm.dt.TransformationMatrix(matrix)
    r_euler = matrix.getRotation()
    r_euler.setDisplayUnit("degrees")
    return r_euler


def get_world_matrix(node, negate_rotate_axis=True):
    if not isinstance(node, pm.PyNode):
        node = pm.PyNode(node)
    if isinstance(node, pm.nt.Transform):
        wm = pm.dt.TransformationMatrix(node.wm.get())
        if negate_rotate_axis:
            r = pm.dt.EulerRotation(cmds.xform(node.longName(), q=True, ws=True, ro=True))
            wm.setRotation(r, node.getRotationOrder())
        return wm
    else:
        return pm.dt.TransformationMatrix()


def set_world_matrix(node, matrix, translate=True, rotate=True, scale=True):
    """
    Set the world matrix of a node.
    """
    if translate and rotate and scale:
        # set the full matrix
        cmds.xform(node.longName(), matrix=[c for r in matrix for c in r], worldSpace=True)
    else:
        # note that setting the components individually is more expensive, especially calculating scale
        if not isinstance(matrix, pm.dt.TransformationMatrix):
            matrix = pm.dt.TransformationMatrix(matrix)

        # only set some components
        if translate:
            cmds.xform(node.longName(), translation=matrix.getTranslation("world"), worldSpace=True)
        if rotate:
            # convert the rotation order
            rotate_order = node.getRotationOrder()
            if rotate_order != matrix.rotationOrder():
                matrix.reorderRotation(rotate_order)
            # note that this method does not handle matching the global rotation with non-zero rotate axis,
            # if that is needed, set the full matrix instead
            rotation = get_euler_rotation_from_matrix(matrix)
            cmds.xform(node.longName(), rotation=rotation, worldSpace=True)
        if scale:
            local_scale_matrix = matrix * node.pim.get()
            cmds.xform(node.longName(), scale=local_scale_matrix.getScale("world"))


def match_world_matrix(leader: pm.nt.Transform, *followers: pm.nt.Transform):
    """
    Set the world matrix of one or more nodes to match a leader's world matrix.

    Args:
        leader: A transform
        followers: One or more transforms to update
    """
    world_mtx = leader.wm.get()
    for follower in followers:
        set_world_matrix(follower, world_mtx)


def get_relative_matrix(node, base_node):
    """
    Return the matrix of a node relative to a base node.

    Args:
        node (PyNode): The node to retrieve the matrix from
        base_node (PyNode): The node to which the matrix will be relative
    """
    return node.wm.get() * base_node.wm.get().inverse()


def set_relative_matrix(node, matrix, base_node):
    """
    Set the world matrix of a node, given a matrix that
    is relative to a different base node.

    Args:
        node (PyNode): The node to modify
        matrix (Matrix): A matrix relative to the base node.
        base_node (PyNode): The node that the matrix is relative to.
    """
    set_world_matrix(node, matrix * base_node.wm.get())


def get_translation_midpoint(a, b):
    """
    Return a vector representing the middle point between the
    world translation of two nodes.

    Args:
        a: A transform node
        b: A transform node
    """
    ta = a.getTranslation(ws=True)
    tb = b.getTranslation(ws=True)
    return (ta + tb) * 0.5


def get_scale_matrix(matrix):
    """
    Return a matrix representing only the scale of a TransformationMatrix
    """
    s = pm.dt.TransformationMatrix(matrix).getScale("world")
    return pm.dt.Matrix((s[0], 0, 0), (0, s[1], 0), (0, 0, s[2]))


def get_rotation_matrix(matrix):
    """
    Return a matrix representing only the rotation of a TransformationMatrix
    """
    return pm.dt.TransformationMatrix(matrix).euler.asMatrix()


def normalize_euler_rotations(node):
    """
    Modify the rotation of a transform node such that its euler
    rotations are in the range of 0..360
    """
    rotation = node.r.get()
    rotation.x %= 360
    rotation.y %= 360
    rotation.z %= 360
    node.r.set(rotation)


# Axis Utils
# ----------


def get_axis(value):
    """
    Returns a pm.dt.Vector.Axis for the given value

    Args:
        value: Any value representing an axis, accepts 0, 1, 2, 3, x, y, z, w
            as well as pm.dt.Vector.Axis objects
    """
    if isinstance(value, pm.util.EnumValue) and value.enumtype == pm.dt.Vector.Axis:
        return value
    elif isinstance(value, int):
        return pm.dt.Vector.Axis[value]
    elif isinstance(value, str):
        for k in pm.dt.Vector.Axis.keys():
            if k.startswith(value):
                return getattr(pm.dt.Vector.Axis, k)


def get_axis_vector(axis, sign=1):
    """
    Return a vector for a signed axis
    """
    i = int(axis)
    v = [0, 0, 0]
    v[i] = 1 * (1 if sign >= 0 else -1)
    return tuple(v)


def get_other_axes(value, include_w=False):
    """
    Return a list of all other axes other than the given axis.

    Args:
        value: Any value representing an axis, accepts 0, 1, 2, 3, x, y, z, w
            as well as pm.dt.Vector.Axis objects.
        include_w: If True, include the W axis.
    """
    axis = get_axis(value)
    if axis is not None:
        skip = [axis.index] + ([] if include_w else [3])
        return [a for a in pm.dt.Vector.Axis.values() if a.index not in skip]


def get_closest_aligned_axis(matrix, axis=0):
    """
    Given a matrix, find and return the signed axis
    that is most aligned with a specific axis.

    Args:
        matrix: A transformation matrix
        axis: The axis to check against

    Returns (axis, sign)
    """
    best_val = None
    best_axis = None
    for a in range(3):
        val = matrix[a][axis]
        if best_val is None or abs(val) > abs(best_val):
            best_val = val
            best_axis = a
    return get_axis(best_axis), 1 if best_val >= 0 else -1


def get_closest_aligned_axes(matrix):
    """
    Given a matrix, find and return signed axes closest to
    the x, y, and z world axes.

    Args:
        matrix: A transformation matrix

    Returns ((axisX, signX), (axisY, signY), (axisZ, signZ))
    """
    x, sign_x = get_closest_aligned_axis(matrix, 0)
    y, sign_y = get_closest_aligned_axis(matrix, 1)
    z, sign_z = get_closest_aligned_axis(matrix, 2)
    return (x, sign_x), (y, sign_y), (z, sign_z)


def get_closest_aligned_relative_axis(node_a, node_b, axis=0):
    """
    Return the signed axis of node A that is most aligned with an axis of node B.

    Returns (axis, sign)
    """
    return get_closest_aligned_axis(node_a.wm.get() * node_b.wim.get(), axis)


def are_nodes_aligned(node_a, node_b):
    """
    Return True if two nodes are roughly aligned, meaning
    their axes point mostly in the same directions.
    """
    signed_axes = get_closest_aligned_axes(node_a.wm.get() * node_b.wim.get())
    for i, (axis, sign) in enumerate(signed_axes):
        if i != axis or sign != 1:
            return False
    return True


# Node Coloring
# -------------


def get_override_color(node) -> Optional[LinearColor]:
    """
    Return the override color of a node.

    Args:
        node (PyNode): A transform node

    Returns:
        The color (RGB tuple), or None if color is not overridden.
    """
    shapes = node.getChildren(s=True)
    for shape in shapes:
        if shape.overrideEnabled.get() and shape.overrideRGBColors.get():
            return LinearColor.from_seq(shape.overrideColorRGB.get())


def set_override_color(node, color: LinearColor, skip_enable_overrides=False):
    """
    Set the override color of a node

    Args:
        node (PyNode): A transform node
        color (tuple of float): An RGB color, 0..1
        skip_enable_overrides (bool): If True, skip enabling the overrides,
            just set the color. Faster if overrides are already enabled.
    """
    shapes = node.getChildren(s=True)

    for shape in shapes:
        if not skip_enable_overrides:
            shape.overrideEnabled.set(True)
            shape.overrideRGBColors.set(True)

        shape.overrideColorRGB.set(color)


def disable_color_override(node):
    """
    Disable drawing overrides for a node and all its shapes.

    Args:
        node (PyNode): A transform node
    """
    shapes = node.getChildren(s=True)
    for shape in [node] + shapes:
        shape.overrideEnabled.set(False)
        shape.overrideRGBColors.set(False)
        shape.overrideColorRGB.set((0, 0, 0))
