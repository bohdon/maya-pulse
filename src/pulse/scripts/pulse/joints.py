
import pymel.core as pm

from . import nodes
from . import math

__all__ = [
    'centerJoint',
    'fixupJointOrient',
    'getChildJoints',
    'getEndJoints',
    'getIKPoleVectorAndMidPoint',
    'getJointMatrices',
    'getParentJoint',
    'getRootJoint',
    'insertJoints',
    'matchJointRotationToOrient',
    'orientIKJoints',
    'orientJoint',
    'orientJointCustom',
    'orientJointToWorld',
    'rotateJointOrient',
    'setJointMatrices',
    'setJointParent',
    'setJointRotationMatrix',
]


def getRootJoint(jnt):
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


def getParentJoint(jnt):
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
            return getParentJoint(parent)


def getChildJoints(jnt):
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
            result.extend(getChildJoints(child))
    return result


def getEndJoints(jnt):
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
            result.extend(getEndJoints(child))
    return result


def setJointParent(child, parent):
    """
    Parent the given `child` joint to `parent`. Handles parenting the joint
    directly rather than inserting a buffer transform.

    Args:
        child: A joint to be parented
        parent: A joint to be the new parent of child
    """
    pm.parent(child, parent, a=True, s=True)


def insertJoints(childJnt, count=1):
    """
    Insert one or more joints as parents of a joint.

    Args:
        childJnt: A Joint node, the inserted joint will be a parent to this joint
    """
    result = []
    pm.select(cl=True)
    parentJnt = childJnt.getParent()
    if parentJnt is None:
        pm.warning('Cannot insert joints for a joint without a parent')
        return result
    startPosition = parentJnt.getTranslation(space='world')
    endPosition = childJnt.getTranslation(space='world')
    print(startPosition, endPosition)
    joints = [parentJnt]
    rad = parentJnt.radius.get()
    for i in range(count):
        jointPos = (endPosition - startPosition) * \
            (float(i+1)/float(count+1)) + startPosition
        j = pm.joint(p=jointPos)
        setJointParent(j, joints[-1])
        j.radius.set(rad)
        pm.joint(j, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True)
        result.append(j)
        joints.append(j)
    setJointParent(childJnt, joints[-1])
    return result


def centerJoint(jnt, child=None):
    """
    Center a joint between its parent and child.

    Args:
        jnt (PyNode): A joint node to be centered
        child: An optional child joint, necessary if the joint has
            more than one child
    """
    parent = jnt.getParent()
    if not isinstance(parent, pm.nt.Joint):
        raise ValueError(
            '{0} is not a child of a joint and cannot be centered'.format(jnt))
    if child is None:
        children = jnt.getChildren(typ='joint')
        if not children:
            raise ValueError(
                '{0} has no child joints and cannot be centered'.format(jnt))
        child = children[0]
    elif not isinstance(child, pm.nt.Joint):
        raise TypeError('child must be a joint')
    mid = nodes.getTranslationMidpoint(parent, child)
    pm.move(jnt, mid, ws=True, pcp=True)


def getJointMatrices(jnt):
    """
    Return the WorldMatrix, Rotation, RotationAxis, and
    JointOrientation matrices for a joint.
    """
    r = pm.dt.EulerRotation(jnt.r.get()).asMatrix()
    ra = pm.dt.EulerRotation(jnt.ra.get()).asMatrix()
    jo = pm.dt.EulerRotation(jnt.jo.get()).asMatrix() * jnt.pm.get()
    return jnt.wm.get(), r, ra, jo


def setJointMatrices(jnt, matrix, r, ra, jo, translate=True, rotate=True):
    """
    Set the matrices on the given joint.
    TODO: make this also affect scale
    """
    matrix = matrix * jnt.pim.get()
    if rotate:
        jo = jo * jnt.pim.get()
        rEuler = pm.dt.TransformationMatrix(r).euler
        raEuler = pm.dt.TransformationMatrix(ra).euler
        joEuler = pm.dt.TransformationMatrix(jo).euler
        rEuler.unit = raEuler.unit = joEuler.unit = 'degrees'
        pm.cmds.setAttr(jnt + '.r', *rEuler)
        pm.cmds.setAttr(jnt + '.ra', *raEuler)
        pm.cmds.setAttr(jnt + '.jo', *joEuler)
    if translate:
        pm.cmds.setAttr(jnt + '.t', *matrix[3][:3])


def setJointRotationMatrix(jnt, matrix):
    """
    Set the rotation matrix of a joint. This is done by setting the joint
    orient and rotation axes, rather than setting the rotation (?).

    This affects the translate and scale axes, which means children's positions
    must be updated.  Normal joint orientation only affects the rotation.

    """
    # TODO: more clear and specific doc string

    # store child matrices
    children = getChildJoints(jnt)
    matrices = [getJointMatrices(j) for j in children]
    # adjust matrices and apply
    # we dont want to change JO, just need to adjust RA
    wm, r, ra, jo = getJointMatrices(jnt)
    # solve for RA
    r = pm.dt.Matrix()
    ra = matrix * r.inverse() * jo.inverse()
    setJointMatrices(jnt, wm, r, ra, jo)


def rotateJointOrient(joint, rotation):
    """
    Rotate the orientation of a joint

    Args:
        joint (Joint): The joint to modify
        rotation (Vector): The rotation to apply to the orient
    """
    pm.rotate(joint.rotateAxis, rotation, r=True, os=True)


def orientJointToWorld(joint):
    """
    Orient the joint to match the world aligned axes
    """
    wm, r, ra, jo = getJointMatrices(joint)
    # set jo to identity
    jo = pm.dt.Matrix()
    # solve for RA
    ra = wm * r.inverse() * jo.inverse()
    setJointMatrices(joint, wm, r, ra, jo)


def orientJoint(joint, axisOrder='xyz', upAxisStr='y', **kwargs):
    """
    Orient the joint to point down the bone

    Args:
        axisOrder (str): The axis order for orienting, e.g. 'xyz', 'zyx', ...
        upAxisStr (str): The axis of the node that should be pointing up,
            represented as a string, e.g. 'x', 'y', 'z'
        kwargs: Any valid kwargs for the `joint` orient command
    """
    if joint.numChildren() > 0:
        # secondary axis orient is in the format 'xup', 'ydown', etc...
        saoStr = upAxisStr + 'up'
        pm.joint(joint, e=True, oj=axisOrder, sao=saoStr, **kwargs)
    else:
        # zero out rotations of end joints
        joint.jo.set([0, 0, 0])


def orientJointCustom(joint, aimVector, upVector, aimAxis='x', upAxis='y', preserveChildren=False):
    """
    Orient a joint to point the aimAxis down aimVector, keeping upAxis as closely aligned to upVector
    as possible. The third axis will be computed.
    """
    children = getChildJoints(joint)

    # keep track of child positions
    if preserveChildren:
        childMatrices = [getJointMatrices(j) for j in children]

    # convert the two axes into a rotation matrix
    if aimAxis == 'x':
        if upAxis == 'y':
            newMtx = math.makeMatrixFromXY(aimVector, upVector)
        elif upAxis == 'z':
            newMtx = math.makeMatrixFromXZ(aimVector, upVector)
        else:
            raise NotImplementedError
    else:
        raise NotImplementedError

    # set the new rotation matrix on the joint, removing any rotate or rotateAxis values
    setJointMatrices(joint, newMtx, pm.dt.Matrix(),
                     pm.dt.Matrix(), newMtx, translate=False)

    # restore child positions
    if preserveChildren:
        for child, childm in zip(children, childMatrices):
            setJointMatrices(child, *childm)


def orientIKJoints(endJoint, aimAxis='x', poleAxis='y', preserveChildren=False):
    """
    Orient the two parent joints of the given end joint to line up with the IK plane
    created by the triangle between all three joints.

    Args:
        endJoint (Joint): The end joint, the two parent joints will be modified
        aimAxis (str): The axis to aim down the bone, default is 'x'
        poleAxis (str): The axis to aim along the ik pole vector
    """
    midJoint = endJoint.getParent()
    rootJoint = midJoint.getParent()

    endPos = endJoint.getTranslation(space='world')
    midPos = midJoint.getTranslation(space='world')
    rootPos = rootJoint.getTranslation(space='world')

    # get the aim-down-bone vectors
    rootToMidVector = midPos - rootPos
    midToEndVector = endPos - midPos

    # get the pole vector
    poleVector, _ = getIKPoleVectorAndMidPoint(endJoint)

    orientJointCustom(rootJoint, aimVector=rootToMidVector, upVector=poleVector,
                      aimAxis=aimAxis, upAxis=poleAxis,
                      preserveChildren=preserveChildren)
    orientJointCustom(midJoint, aimVector=midToEndVector, upVector=poleVector,
                      aimAxis=aimAxis, upAxis=poleAxis,
                      preserveChildren=preserveChildren)


def fixupJointOrient(joint, aimAxis='x', keepAxis='y', preserveChildren=False):
    """
    Orient the joint to point down the bone, preserving one existing axis of the current orientation.

    Args:
        joint (Joint): The joint to modify
        aimAxis (str): The axis to aim down the bone, default is 'x'
        keepAxis (str): The axis to preserve, default is 'y'
    """
    children = getChildJoints(joint)
    if not children:
        raise ValueError("%s has no children" % joint)

    # use first child for aiming down bone
    child = children[0]

    # get the down-bone basis vector
    jointPos = joint.getTranslation(space='world')
    childPos = child.getTranslation(space='world')
    aimAxisVector = childPos - jointPos

    # get the keepAxis basis vector
    keepAxisIndex = {'x': 0, 'y': 1, 'z': 2}[keepAxis]
    keepAxisVector = joint.wm.get()[keepAxisIndex][0:3]

    orientJointCustom(joint, aimVector=aimAxisVector, upVector=keepAxisVector,
                      aimAxis=aimAxis, upAxis=keepAxis,
                      preserveChildren=preserveChildren)


def matchJointRotationToOrient(joint, preserveChildren=False):
    if preserveChildren:
        children = getChildJoints(joint)
        childMatrices = [getJointMatrices(j) for j in children]

    _, _, _, jo = getJointMatrices(joint)
    setJointRotationMatrix(joint, jo)

    if preserveChildren:
        for child, childm in zip(children, childMatrices):
            setJointMatrices(child, *childm)


def getIKPoleVectorAndMidPoint(endJoint):
    """
    Return the pole vector and corresponding mid point between the root of an ik joint
    setup and the given end joint
    """
    midJoint = endJoint.getParent()
    if not midJoint:
        raise ValueError("%s has no parent joint" % endJoint)
    rootJoint = midJoint.getParent()
    if not rootJoint:
        raise ValueError("%s has no parent joint" % rootJoint)

    endPos = endJoint.getTranslation(space='world')
    midPos = midJoint.getTranslation(space='world')
    rootPos = rootJoint.getTranslation(space='world')

    # get the direction betwen root and end
    ikDirection = (endPos - rootPos).normal()
    # these are also the point-down-bone vectors
    rootToMidVector = midPos - rootPos
    # get point along the line between root..end that lines up with mid joint
    midPoint = rootPos + ikDirection.dot(rootToMidVector) * ikDirection
    # use poleVector for pole axis for both mid and root joint orientation
    poleVector = (midPos - midPoint).normal()

    return poleVector, midPoint
