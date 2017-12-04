
import pymel.core as pm

from mayacoretools import preservedSelection

import pulse.nodes

__all__ = [
    'centerJoint',
    'centerSelectedJoints',
    'getChildJoints',
    'getParentJoint',
    'getRootJoint',
    'insertJointForSelected',
    'insertJoints',
    'setJointParent',
    'disableSegmentScaleCompensateForSelected',
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
        jnt: A Joint node
    """
    result = []
    children = jnt.getChildren()
    for child in children:
        if isinstance(child, pm.nt.Joint):
            result.append(child)
        else:
            result.extend(getChildJoints(child))
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
        jointPos = (endPosition - startPosition) * (float(i+1)/float(count+1)) + startPosition
        j = pm.joint(p=jointPos)
        setJointParent(j, joints[-1])
        j.radius.set(rad)
        pm.joint(j, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True)
        result.append(j)
        joints.append(j)
    setJointParent(childJnt, joints[-1])
    return result


def insertJointForSelected(count=1):
    """
    Insert joints above the selected joint
    """
    result = []
    for s in pm.selected():
        result.extend(insertJoints(s, count))
    pm.select(result)


def centerJoint(jnt, child=None):
    """
    Center a joint between its parent and child.

    Args:
        jnt: A Joint node to be centered
        child: An optional child joint, necessary if the joint has
            more than one child
    """
    parent = jnt.getParent()
    if not isinstance(parent, pm.nt.Joint):
        raise ValueError('{0} is not a child of a joint and cannot be centered'.format(jnt))
    if child is None:
        children = jnt.getChildren(typ='joint')
        if not children:
            raise ValueError('{0} has no child joints and cannot be centered'.format(jnt))
        child = children[0]
    elif not isinstance(child, pm.nt.Joint):
        raise TypeError('child must be a joint')
    mid = pulse.nodes.getTranslationMidpoint(parent, child)
    pm.move(jnt, mid, ws=True, pcp=True)


def centerSelectedJoints():
    """
    Center the selected joint
    """
    for s in pm.selected():
        centerJoint(s)


def disableSegmentScaleCompensateForSelected():
    """
    Disable segment scale compensation on the selected joints
    """
    for jnt in pm.selected():
        if jnt.nodeType() == 'joint':
            jnt.ssc.set(False)
