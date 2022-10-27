import pymel.core as pm

from . import math
from . import nodes


def get_root_joint(jnt):
    """
    Get the top most joint for the given joint in a joint chain

    Args:
        jnt: A Joint node
    """
    if jnt.nodeType() != 'joint':
        return
    parent = jnt.getParent()
    while parent and parent.nodeType() == 'joint':
        jnt = parent
        parent = parent.getParent()
    return jnt


def get_parent_joint(jnt):
    """
    Returns the first parent of a given joint that is also a joint.

    Args:
        jnt: A Joint node
    """
    parent = jnt.getParent()
    if parent:
        if isinstance(parent, pm.nt.Joint):
            return parent
        else:
            return get_parent_joint(parent)


def get_child_joints(jnt):
    """
    Recurse through children to find and return any children joints,
    even if they are not immediate children. Will include the first
    joint found for each branch.

    Args:
        jnt (PyNode): A joint node
    """
    result = []
    children = jnt.getChildren()
    for child in children:
        if isinstance(child, pm.nt.Joint):
            result.append(child)
        else:
            result.extend(get_child_joints(child))
    return result


def get_end_joints(jnt):
    """
    Recurse through children and return all joints that have no joint children.

    Args:
        jnt (PyNode): A joint node
    """
    result = []
    children = jnt.listRelatives(children=True, typ='joint')
    if not children:
        result.append(jnt)
    else:
        for child in children:
            result.extend(get_end_joints(child))
    return result


def set_joint_parent(child, parent):
    """
    Parent the given `child` joint to `parent`. Handles parenting the joint
    directly rather than inserting a buffer transform.

    Args:
        child: A joint to be parented.
        parent: A joint to be the new parent of child.
    """
    pm.parent(child, parent, a=True, s=True)


def insert_joints(child_jnt, count=1):
    """
    Insert one or more joints as parents of a joint.

    Args:
        child_jnt: A Joint node, the inserted joint will be a parent to this joint.
        count: The number of joints to insert.
    """
    result = []
    pm.select(cl=True)
    parent_jnt = child_jnt.getParent()
    if parent_jnt is None:
        pm.warning('Cannot insert joints for a joint without a parent')
        return result
    start_position = parent_jnt.getTranslation(space='world')
    end_position = child_jnt.getTranslation(space='world')
    joints = [parent_jnt]
    rad = parent_jnt.radius.get()
    for i in range(count):
        joint_pos = (end_position - start_position) * (float(i + 1) / float(count + 1)) + start_position
        j = pm.joint(p=joint_pos)
        set_joint_parent(j, joints[-1])
        j.radius.set(rad)
        pm.joint(j, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True)
        result.append(j)
        joints.append(j)
    set_joint_parent(child_jnt, joints[-1])
    return result


def center_joint(jnt, child=None):
    """
    Center a joint between its parent and child.

    Args:
        jnt (PyNode): A joint node to be centered
        child: An optional child joint, necessary if the joint has
            more than one child
    """
    parent = jnt.getParent()
    if not isinstance(parent, pm.nt.Joint):
        raise ValueError(f'{jnt} is not a child of a joint and cannot be centered')
    if child is None:
        children = jnt.getChildren(typ='joint')
        if not children:
            raise ValueError(f'{jnt} has no child joints and cannot be centered')
        child = children[0]
    elif not isinstance(child, pm.nt.Joint):
        raise TypeError('child must be a joint')
    mid = nodes.get_translation_midpoint(parent, child)
    pm.move(jnt, mid, ws=True, pcp=True)


def freeze_joints(joint, rotate=True, scale=True):
    """
    Freeze rotates and scales on a joint hierarchy without creating intermediate transform nodes

    Args:
        rotate (bool): If true, freeze rotations
        scale (bool): If true, freeze scales
        joint (pm.PyNode): A Transform node
    """
    joints = [joint]
    joints.extend(nodes.get_descendants_top_to_bottom(joint))

    if rotate:
        # freeze rotates
        for node in joints:
            orient_joint_to_rotation(node, True)

    if scale:
        # freeze scales by copying translations, zeroing out scales, then re-applying translates
        world_matrices = []
        for node in joints:
            world_matrices.append(node.wm.get())

        for (node, mtx) in zip(joints, world_matrices):
            node.s.set((1, 1, 1))
            pm.xform(node, translation=mtx.translate, worldSpace=True)


def get_joint_matrices(jnt):
    """
    Return the WorldMatrix, Rotation, RotationAxis, and
    JointOrientation matrices for a joint.
    """
    r = pm.dt.EulerRotation(jnt.r.get()).asMatrix()
    ra = pm.dt.EulerRotation(jnt.ra.get()).asMatrix()
    jo = pm.dt.EulerRotation(jnt.jo.get()).asMatrix() * jnt.pm.get()
    return jnt.wm.get(), r, ra, jo


def set_joint_matrices(jnt, matrix, r, ra, jo, translate=True, rotate=True):
    """
    Set the matrices on the given joint.
    TODO: make this also affect scale
    """
    matrix = matrix * jnt.pim.get()
    if rotate:
        jo = jo * jnt.pim.get()
        r_euler = pm.dt.TransformationMatrix(r).euler
        ra_euler = pm.dt.TransformationMatrix(ra).euler
        jo_euler = pm.dt.TransformationMatrix(jo).euler
        r_euler.unit = ra_euler.unit = jo_euler.unit = 'degrees'
        pm.cmds.setAttr(jnt + '.r', *r_euler)
        pm.cmds.setAttr(jnt + '.ra', *ra_euler)
        pm.cmds.setAttr(jnt + '.jo', *jo_euler)
    if translate:
        pm.cmds.setAttr(jnt + '.t', *matrix[3][:3])


def set_joint_rotation_matrix(jnt, matrix):
    """
    Set the rotation matrix of a joint. This is done by setting the joint
    orient and rotation axes, rather than setting the rotation (?).

    This affects the translate and scale axes, which means children's positions
    must be updated. Normal joint orientation only affects the rotation.

    """
    # TODO: more clear and specific doc string

    # store child matrices
    children = get_child_joints(jnt)
    matrices = [get_joint_matrices(j) for j in children]
    # adjust matrices and apply
    # we don't want to change JO, just need to adjust RA
    wm, r, ra, jo = get_joint_matrices(jnt)
    # solve for RA
    r = pm.dt.Matrix()
    ra = matrix * r.inverse() * jo.inverse()
    set_joint_matrices(jnt, wm, r, ra, jo)


def rotate_joint_orient(joint, rotation):
    """
    Rotate the orientation of a joint

    Args:
        joint (Joint): The joint to modify
        rotation (Vector): The rotation to apply to the orient
    """
    pm.rotate(joint.rotateAxis, rotation, r=True, os=True)


def orient_joint_to_world(joint):
    """
    Orient the joint to match the world aligned axes
    """
    wm, r, ra, jo = get_joint_matrices(joint)
    # set jo to identity
    jo = pm.dt.Matrix()
    # solve for RA
    ra = wm * r.inverse() * jo.inverse()
    set_joint_matrices(joint, wm, r, ra, jo)


def orient_joint(joint: pm.nt.Joint, axis_order='xyz', up_axis_str='y', **kwargs):
    """
    Orient the joint to point down the bone

    Args:
        joint: The joint to orient.
        axis_order (str): The axis order for orienting, e.g. 'xyz', 'zyx', ...
        up_axis_str (str): The axis of the node that should be pointing up,
            represented as a string, e.g. 'x', 'y', 'z'
        kwargs: Any valid kwargs for the `joint` orient command
    """
    if joint.numChildren() > 0:
        # secondary axis orient is in the format 'xup', 'ydown', etc...
        sao_str = up_axis_str + 'up'
        pm.joint(joint, e=True, oj=axis_order, sao=sao_str, **kwargs)
    else:
        # zero out rotations of end joints
        joint.jo.set([0, 0, 0])


def orient_joint_custom(joint, aim_vector, up_vector, aim_axis='x', up_axis='y', preserve_children=False):
    """
    Orient a joint to point the aim_axis down aim_vector, keeping up_axis as closely aligned to up_vector
    as possible. The third axis will be computed.
    """
    children = get_child_joints(joint)

    # keep track of child positions
    if preserve_children:
        child_matrices = [get_joint_matrices(j) for j in children]

    # convert the two axes into a rotation matrix
    if aim_axis == 'x':
        if up_axis == 'y':
            new_mtx = math.make_matrix_from_xy(aim_vector, up_vector)
        elif up_axis == 'z':
            new_mtx = math.make_matrix_from_xz(aim_vector, up_vector)
        else:
            raise NotImplementedError
    else:
        raise NotImplementedError

    # set the new rotation matrix on the joint, removing any rotate or rotateAxis values
    set_joint_matrices(joint, new_mtx, pm.dt.Matrix(), pm.dt.Matrix(), new_mtx, translate=False)

    # restore child positions
    if preserve_children:
        for child, child_mtx in zip(children, child_matrices):
            set_joint_matrices(child, *child_mtx)


def orient_ik_joints(end_joint, aim_axis='x', pole_axis='y', preserve_children=False):
    """
    Orient the two parent joints of the given end joint to line up with the IK plane
    created by the triangle between all three joints.

    Args:
        end_joint (Joint): The end joint, the two parent joints will be modified
        aim_axis (str): The axis to aim down the bone, default is 'x'
        pole_axis (str): The axis to aim along the ik pole vector
        preserve_children: If true, prevent child joints from moving.
    """
    mid_joint = end_joint.getParent()
    root_joint = mid_joint.getParent()

    end_pos = end_joint.getTranslation(space='world')
    mid_pos = mid_joint.getTranslation(space='world')
    root_pos = root_joint.getTranslation(space='world')

    # get the aim-down-bone vectors
    root_to_mid_vector = mid_pos - root_pos
    mid_to_end_vector = end_pos - mid_pos

    # get the pole vector
    pole_vector, _ = get_ik_pole_vector_and_mid_point_for_joint(end_joint)

    orient_joint_custom(root_joint, aim_vector=root_to_mid_vector, up_vector=pole_vector,
                        aim_axis=aim_axis, up_axis=pole_axis, preserve_children=preserve_children)
    orient_joint_custom(mid_joint, aim_vector=mid_to_end_vector, up_vector=pole_vector,
                        aim_axis=aim_axis, up_axis=pole_axis, preserve_children=preserve_children)


def orient_joint_to_parent(joint, preserve_children=False):
    """
    Orient a joint to match it's parent joint orientation.
    """
    if preserve_children:
        children = get_child_joints(joint)
        child_matrices = [get_joint_matrices(j) for j in children]

    parent = joint.getParent()
    if parent:
        wm = parent.wm.get()
    else:
        wm = pm.dt.Matrix()

    set_joint_matrices(joint, wm, pm.dt.Matrix(), pm.dt.Matrix(), wm, translate=False)

    if preserve_children:
        for child, child_mtx in zip(children, child_matrices):
            set_joint_matrices(child, *child_mtx)


def orient_joint_to_rotation(joint, preserve_children=False):
    """
    Orient a joint to match its current rotation.
    This is synonymous with freezing a joint's rotation.

    Args:
        joint:
        preserve_children:
    """
    if preserve_children:
        children = get_child_joints(joint)
        child_matrices = [get_joint_matrices(j) for j in children]

    wm, r, ra, jo = get_joint_matrices(joint)
    # set the joint matrices, using world matrix for joint orient, and clearing the rest
    set_joint_matrices(joint, wm, pm.dt.Matrix(), pm.dt.Matrix(), wm, translate=False)

    if preserve_children:
        for child, childMtx in zip(children, child_matrices):
            set_joint_matrices(child, *childMtx)


def fixup_joint_orient(joint, aim_axis='x', keep_axis='y', preserve_children=False):
    """
    Orient the joint to point down the bone, preserving one existing axis of the current orientation.

    Args:
        joint (Joint): The joint to modify
        aim_axis (str): The axis to aim down the bone, default is 'x'
        keep_axis (str): The axis to preserve, default is 'y'
    """
    children = get_child_joints(joint)
    if not children:
        raise ValueError("%s has no children" % joint)

    # use first child for aiming down bone
    child = children[0]

    # get the down-bone basis vector
    joint_pos = joint.getTranslation(space='world')
    child_pos = child.getTranslation(space='world')
    aim_axis_vector = child_pos - joint_pos

    # get the keep_axis basis vector
    keep_axis_index = {'x': 0, 'y': 1, 'z': 2}[keep_axis]
    keep_axis_vector = joint.wm.get()[keep_axis_index][0:3]

    orient_joint_custom(joint, aim_vector=aim_axis_vector, up_vector=keep_axis_vector,
                        aim_axis=aim_axis, up_axis=keep_axis, preserve_children=preserve_children)


def match_joint_rotation_to_orient(joint, preserve_children=False):
    if preserve_children:
        children = get_child_joints(joint)
        child_matrices = [get_joint_matrices(j) for j in children]

    _, _, _, jo = get_joint_matrices(joint)
    set_joint_rotation_matrix(joint, jo)

    if preserve_children:
        for child, child_mtx in zip(children, child_matrices):
            set_joint_matrices(child, *child_mtx)


def get_ik_pole_vector_and_mid_point_for_joint(end_joint):
    """
    Return the pole vector and corresponding mid-point between the root of an ik joint
    setup and the given end joint

    Returns:
        Tuple of (pole_vector, pole_mid_point)
    """
    mid_joint = end_joint.getParent()
    if not mid_joint:
        raise ValueError("%s has no parent joint" % end_joint)
    root_joint = mid_joint.getParent()
    if not root_joint:
        raise ValueError("%s has no parent joint" % root_joint)

    end = end_joint.getTranslation(space='world')
    mid = mid_joint.getTranslation(space='world')
    root = root_joint.getTranslation(space='world')

    return get_ik_pole_vector_and_mid_point(root, mid, end)


def get_ik_pole_vector_and_mid_point(root: pm.dt.Vector, mid: pm.dt.Vector, end: pm.dt.Vector):
    """
    Return the pole vector and corresponding mid-point between the root and end positions
    of an ik joint chain.

    Args:
        root: The location of the root joint
        mid: The location of the mid joint
        end: The location of the end joint

    Returns:
        Tuple of (pole_vector, pole_mid_point)
    """
    # get the direction between root and end
    ik_direction = (end - root).normal()
    # these are also the point-down-bone vectors
    root_to_mid_vector = mid - root
    # get point along the line between root and end that lines up with mid-joint
    pole_mid_point = root + ik_direction.dot(root_to_mid_vector) * ik_direction
    # get vector from mid-point towards the mid-joint location
    pole_vector = (mid - pole_mid_point).normal()

    return pole_vector, pole_mid_point
