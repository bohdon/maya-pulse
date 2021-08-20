import logging
import os

import maya.cmds as cmds
import pymel.core as pm

LOG = logging.getLogger(__name__)
LOG_LEVEL_KEY = 'PYLOG_%s' % LOG.name.split('.')[0].upper()
LOG.setLevel(os.environ.get(LOG_LEVEL_KEY, 'INFO').upper())


# Node Retrieval
# --------------

def getAllParents(node, includeNode=False):
    """
    Return all parents of a node

    Args:
        node: A node to find parents for
        includeNode: A bool, whether to include the
            given node in the result

    Returns:
        A list of nodes
    """
    if isinstance(node, str):
        split = node.split('|')
        return ['|'.join(split[:i]) for i in reversed(range(2, len(split)))]
    parents = []
    parent = node.getParent()
    if parent is not None:
        parents.append(parent)
        parents.extend(getAllParents(parent))
    if includeNode:
        parents.insert(0, node)
    return parents


def getParentNodes(nodes):
    """
    Returns the top-most parent nodes of all nodes
    in a list.

    Args:
        nodes: A list of nodes
    """
    # TODO: optimize using long names and string matching
    result = []
    for n in nodes:
        if any([p in nodes for p in getAllParents(n)]):
            continue
        result.append(n)
    return result


def getNodeBranch(root, end):
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
    nodes = getAllParents(end)
    nodes.reverse()
    nodes.append(end)
    index = nodes.index(root)
    return nodes[index:]


def duplicateBranch(root, end, parent=None, nameFmt='{0}'):
    """
    Duplicate a node branch from root to end (inclusive).

    Args:
        root (PyNode): The root node of the branch
        end (PyNode): The end node of the branch
        parent (PyNode): The parent parent node of the new node branch
        nameFmt (str): The naming format to use for the new nodes.
            Will be formatted with the name of the original nodes.
    """
    result = []
    allNodes = getNodeBranch(root, end)
    if allNodes is None:
        raise ValueError(
            'Invalid root and end nodes: {0} {1}'.format(root, end))
    nextParent = parent
    for node in allNodes:
        # duplicate only this node
        newNode = pm.duplicate(node, parentOnly=True)[0]
        newNode.rename(nameFmt.format(node.nodeName()))
        newNode.setParent(nextParent)
        # use this node as parent for the next
        nextParent = newNode
        result.append(newNode)
    return result


def getAssemblies(nodes):
    """
    Return any top-level nodes (assemblies) that
    contain a list of nodes

    Args:
        nodes: A list of node long-names. Does not support
            short names or PyNodes.
    """
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]
    return list(set([n[:(n + '|').find('|', 1)] for n in nodes]))


# Transform Parenting
# -------------------

def getDescendantsTopToBottom(node, **kwargs):
    """
    Return a list of all the descendants of a node,
    in hierarchical order, from top to bottom.

    Args:
        node (PyNode): A dag node with children
        **kwargs: Kwargs given to the listRelatives command
    """
    return reversed(node.listRelatives(ad=True, **kwargs))


def getTransformHierarchy(transform, includeParent=True):
    """
    Return a list of (parent, [children]) tuples for a transform
    and all of its descendants.

    Args:
        transform: A Transform node
        includeParent: A bool, when True, the relationship between
            the transform and its parent is included
    """
    result = []
    if includeParent:
        result.append((transform.getParent(), [transform]))

    descendants = transform.listRelatives(ad=True, type='transform')

    for t in [transform] + descendants:
        children = t.getChildren(type='transform')
        if children:
            result.append((t, children))

    return result


def setTransformHierarchy(hierarchy):
    """
    Reparent one or more transform nodes.

    Args:
        hierarchy: A list of (parent, [children]) tuples
    """

    for (parent, children) in hierarchy:
        setParent(children, parent)


def setParent(children, parent):
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
            tops = getParentNodes(conflicts)
            pm.parent(parent, tops[0].getParent())
    args = children[:] + [parent]
    pm.parent(*args)


def parentInOrder(nodes):
    """
    Parent the given nodes to each other in order.
    Leaders then folowers, eg. [A, B, C] -> A|B|C

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
    safeParent = nodes[0].getParent()
    while safeParent in nodes:
        safeParent = safeParent.getParent()
        if safeParent is None:
            # None should never be in the given list of nodes,
            # but this is a failsafe to prevent infinite loop if it is
            break
    setParent(nodes, safeParent)
    # parent all nodes in order
    for i in range(len(nodes) - 1):
        parent, child = nodes[i:i + 2]
        setParent(child, parent)


# Node Creation
# -------------

def createOffsetTransform(node, name='{0}_offset'):
    """
    Create a transform that is inserted as the new parent of a node,
    at the same world location as the node. This effectively transfers
    the local matrix of a node into the new transform, zeroing out
    the attributes of the node (usually for animation). This includes
    absorbing the rotate axis of the node.

    Args:
        node (PyNode): A node to create an offset for
        name (str): The name to use for the new transform. Accepts a single
            format argument which will be the name of `node`
    """
    # create the offset transform
    _name = name.format(node.nodeName())
    offset = pm.createNode('transform', n=_name)

    # parent the offset to the node and reset
    # its local transformation
    offset.setParent(node)
    pm.xform(offset, objectSpace=True,
             translation=[0, 0, 0],
             rotation=[0, 0, 0],
             scale=[1, 1, 1],
             shear=[0, 0, 0],
             )

    # with transforms now absorbed, move offset to be a sibling of the node
    offset.setParent(node.getParent())

    # now parent the node to the new offset, and reset its transform
    node.setParent(offset)
    pm.xform(node, objectSpace=True,
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

def getExpandedAttrNames(attrs):
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
        if attr in ('t', 'r', 'rp', 's', 'sp', 'ra'):
            # translate, rotate, scale and their pivots, also rotate axis
            _attrs.extend([attr + a for a in 'xyz'])
        elif attr in ('sh',):
            # shear
            _attrs.extend([attr + a for a in ('xy', 'xz', 'yz')])
        else:
            # not a known compound attribute
            _attrs.append(attr)
    return _attrs


def safeGetAttr(node, attrName):
    """
    Return an attribute from a node by name.
    Returns None if the attribute does not exist.

    Args:
        node (PyNode): The node with the attribute
        attrName (str): The attribute name
    """
    if node.hasAttr(attrName):
        return node.attr(attrName)


def getCompoundAttrIndex(childAttr):
    """
    Return the index of the given compound child attribute.

    Args:
        childAttr (Attribute): An attribute that is the child of a compount attr
    """
    if not childAttr.isChild():
        raise ValueError("Attribute is not a child of a "
                         "compound attribute: {0}".format(childAttr))
    return childAttr.getParent().getChildren().index(childAttr)


def getAttrDimension(attr):
    """
    Return the dimension of an Attribute

    Args:
        attr (Attribute): The attribute to check
    """
    if attr.isCompound():
        return attr.numChildren()
    else:
        return 1


def getAttrOrValueDimension(attrOrValue):
    """
    Return the dimension of an attribute or
    attribute value (such as a list or tuple)

    Args:
        attrOrValue: An Attribute or value that can be set on an attribute
    """
    if isinstance(attrOrValue, pm.Attribute):
        return getAttrDimension(attrOrValue)
    else:
        # support duck-typed lists
        if not isinstance(attrOrValue, str):
            try:
                return len(attrOrValue)
            except:
                pass
    return 1


# Constraints
# -----------

def setConstraintLocked(constraint, locked):
    """
    Lock all important attributes on a constraint node

    Args:
        constraint: A ParentConstraint or ScaleConstraint node
        locked: A bool, whether to make the constraint locked or unlocked
    """
    attrs = ['nodeState']
    if isinstance(constraint, pm.nt.ScaleConstraint):
        attrs.extend(['offset%s' % a for a in 'XYZ'])
    elif isinstance(constraint, pm.nt.ParentConstraint):
        targets = constraint.target.getArrayIndices()
        for i in targets:
            attrs.extend(['target[%d].targetOffsetTranslate%s' %
                          (i, a) for a in 'XYZ'])
            attrs.extend(['target[%d].targetOffsetRotate%s' % (i, a)
                          for a in 'XYZ'])
    for a in attrs:
        constraint.attr(a).setLocked(locked)


def convertScaleConstraintToWorldSpace(scaleConstraint):
    """
    Modify a scale constraint to make it operate better with
    misaligned axes between the leader and follower by plugging
    the worldMatrix of the leader node into the scale constraint.

    Args:
        scaleConstraint: A ScaleConstraint node
    """
    for i in range(scaleConstraint.target.numElements()):
        inputs = scaleConstraint.target[i].targetParentMatrix.inputs(p=True)
        for input in inputs:
            if input.longName().startswith('parentMatrix'):
                # disconnect and replace with world matrix
                input // scaleConstraint.target[i].targetParentMatrix
                input.node().wm >> scaleConstraint.target[i].targetParentMatrix
                # also disconnect target scale
                scaleConstraint.target[i].targetScale.disconnect()
                break


def fullConstraint(leader, follower):
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


def connectOffsetMatrix(leader, follower, preservePosition=True,
                        preserveTransformValues=True, keepInheritTransform=False):
    """
    Connect the world matrix of a node to the offsetParentMatrix of another node,
    and disable inheritsTransform on the follower, effectively changing the parent
    matrix to the new leader.
    (Maya 2020 and higher)

    Args:
        leader (PyNode or matrix Attribute): A node to use as the leader
        follower (PyNode): A node to use as the follower
        preservePosition (bool): If true, preserve the followers world space position
        preserveTransformValues (bool): If true, preservePosition will not affect the
            current translate, rotate, and scale values of the follower by inserting
            a multMatrix node to handle any existing offsets. This is necessary
            if offsetParentMatrix has a non-identity value, in which case the value
            will be moved into the multMatrix node.
        keepInheritTransform (bool): If true, inheritsTransform will not be changed
    """
    # this order is important because Attributes are subclasses of PyNodes
    if isinstance(leader, pm.Attribute):
        if not leader.type() == 'matrix':
            raise ValueError(
                'Expected matrix attribute, got %s' % leader.type())
        inputMatrix = leader
    elif isinstance(leader, pm.PyNode):
        inputMatrix = leader.wm
    else:
        raise ValueError(
            'Expected PyNode or Attribute for leader, got: %s' % type(leader))

    if not preservePosition:
        inputMatrix >> follower.offsetParentMatrix
        if not keepInheritTransform:
            follower.inheritsTransform.set(False)
    else:
        # remember world matrix
        wm = getWorldMatrix(follower)

        # disable inherit transform to make the connection
        # effectively replace any previous parent matrix
        # contributors, so that the new connection is absolute
        if not keepInheritTransform:
            follower.inheritsTransform.set(False)

        if preserveTransformValues:
            # calculate offset between new leader and follower
            offsetMtx = calculatePreservedOffsetMatrix(
                inputMatrix.get(), wm, follower.m.get())
            # store offset in a new multMatrix node, and connect
            mult = pm.createNode('multMatrix', n='multMatrix_opm_con')
            mult.matrixIn[0].set(offsetMtx)
            inputMatrix >> mult.matrixIn[1]
            mult.matrixSum >> follower.offsetParentMatrix
        else:
            inputMatrix >> follower.offsetParentMatrix
            # restore world matrix (absorbed into local matrix)
            setWorldMatrix(follower, wm)


def calculatePreservedOffsetMatrix(leaderWorldMtx, followerWorldMtx, followerMtx):
    """
    Return an offset matrix between a leader and follower, such that:
        follower.matrix * offsetMatrix * leader.worldMatrix == follower.worldMatrix

    Args:
        leaderWorldMtx (matrix): The matrix to which the new offset will be relative
        followerWorldMtx (matrix): The world matrix that should be preserved
        followerMtx (matrix): The local matrix of the follower node

    Returns:
        A matrix that represents the offset between leaderMatrix and the follower,
        without the follower's local matrix being included.
    """
    return followerMtx.inverse() * followerWorldMtx * leaderWorldMtx.inverse()


def disconnectOffsetMatrix(follower, preservePosition=True,
                           preserveTransformValues=True, keepInheritTransform=False):
    """
    Disconnect any inputs to the offsetParentMatrix of a node,
    and re-enable inheritsTransform.
    (Maya 2020 and higher)

    Args:
        follower (PyNode): A node with input connections to offsetParentMatrix
        preservePosition (bool): If true, preserve the followers world space position
        preserveTransformValues (bool): If true, preservePosition will not affect the
            current translate, rotate, and scale values of the follower by absorbing
            any offset into the follower's offsetParentMatrix.
        keepInheritTransform (bool): If true, inheritsTransform will not be changed
    """
    if not preservePosition:
        follower.opm.disconnect()
        if not keepInheritTransform:
            follower.inheritsTransform.set(True)
    else:
        # remember world matrix
        wm = getWorldMatrix(follower)

        # enable inherit transform so that its as if previously
        # replaced parent matrix contributors are restored
        if not keepInheritTransform:
            follower.inheritsTransform.set(True)

        follower.opm.disconnect()

        if preserveTransformValues:
            # m needs to stay the same, opm will be set to the delta
            # between the new parent matrix (parent node's world matrix,
            # without this nodes opm) and the old follower world matrix.
            pmWithoutOpm = follower.opm.get().inverse() * follower.pm.get()
            deltaToOldOM = follower.im.get() * wm * pmWithoutOpm.inverse()
            follower.opm.set(deltaToOldOM)
        else:
            # zero out opm and restore world matrix
            follower.opm.set(pm.dt.Matrix())
            setWorldMatrix(follower, wm)


# Transform Modification
# ----------------------


def freezeScalesForHierarchy(node):
    """
    Freeze scales on a transform and all its descendants without affecting pivots.
    Does this by parenting all children to the world, freezing, then restoring the hierarchy.

    Args:
        node (pm.PyNode): A Transform node
    """
    hierarchy = getTransformHierarchy(node)
    children = node.listRelatives(ad=True, type='transform')
    for c in children:
        c.setParent(None)
    for n in [node] + children:
        pm.makeIdentity(n, t=False, r=False, s=True, n=False, apply=True)
    setTransformHierarchy(hierarchy)


def freezePivot(transform):
    """
    Freeze the given transform such that its local pivot becomes zero,
    but its world space pivot remains unchanged.

    Args:
        transform: A Transform node
    """
    pivot = pm.dt.Vector(pm.xform(transform, q=True, rp=True, worldSpace=True))
    # asking for worldspace translate gives different result than world space matrix
    # translate. we want the former in this situation because we will be setting
    # with the same world space translate method
    translate = pm.dt.Vector(
        pm.xform(transform, q=True, t=True, worldSpace=True))
    parentTranslate = pm.dt.Vector()
    parent = transform.getParent()
    if parent:
        # we want the world space matrix translate of the parent
        # because thats the real location that zeroed out child transforms would exist.
        # note that the world space translate (not retrieving matrix) can be a different value
        parentTranslate = pm.dt.Matrix(
            pm.xform(parent, q=True, m=True, worldSpace=True)).translate
    # move current pivot to the parents world space location
    pm.xform(transform, t=(translate - pivot + parentTranslate), ws=True)
    # now that the transform is at the same world space position as its parent, freeze it
    pm.makeIdentity(transform, t=True, apply=True)
    # restore world pivot position with translation
    pm.xform(transform, t=pivot, ws=True)


def freezePivotsForHierarchy(transform):
    """
    Freeze pivots on a transform and all its descendants.

    Args:
        transform: A Transform node
    """
    hierarchy = getTransformHierarchy(transform)
    children = transform.listRelatives(ad=True, type='transform')
    for c in children:
        c.setParent(None)
    for n in [transform] + children:
        freezePivot(n)
    setTransformHierarchy(hierarchy)


def freezeOffsetMatrix(transform):
    """
    Freeze the translate, rotate, and scale of a transform
    by moving its current local matrix values into its
    offsetParentMatrix. This operation is idempotent.
    (Maya 2020 and higher)
    """
    if not transform.offsetParentMatrix.isSettable():
        LOG.warning(
            'Cannot freeze %s offset matrix, offsetParentMatrix is not settable', transform)
        return
    localMtx = transform.m.get()
    offsetMtx = transform.offsetParentMatrix.get()
    newOffsetMtx = localMtx * offsetMtx
    transform.offsetParentMatrix.set(newOffsetMtx)
    transform.setMatrix(pm.dt.Matrix())


def freezeOffsetMatrixForHierarchy(transform):
    children = transform.listRelatives(ad=True, type='transform')
    for node in [transform] + children:
        freezeOffsetMatrix(node)


def unfreezeOffsetMatrix(transform):
    """
    Unfreeze the translate, rotate, and scale of a transform
    by moving its current offset parent matrix values into its
    translate, rotate, and scale. This operation is idempotent.
    (Maya 2020 and higher)
    """
    if not transform.offsetParentMatrix.isSettable():
        LOG.warning(
            'Cannot unfreeze %s offset matrix, offsetParentMatrix is not settable', transform)
        return
    localMtx = transform.m.get()
    offsetMtx = transform.offsetParentMatrix.get()
    newLocalMtx = localMtx * offsetMtx
    transform.setMatrix(newLocalMtx)
    transform.offsetParentMatrix.set(pm.dt.Matrix())


def unfreezeOffsetMatrixForHierarchy(transform):
    children = transform.listRelatives(ad=True, type='transform')
    for node in [transform] + children:
        unfreezeOffsetMatrix(node)


def getEulerRotationFromMatrix(matrix):
    """
    Return the euler rotation in degrees of a matrix
    """
    if not isinstance(matrix, pm.dt.TransformationMatrix):
        matrix = pm.dt.TransformationMatrix(matrix)
    rEuler = matrix.getRotation()
    rEuler.setDisplayUnit('degrees')
    return rEuler


def getWorldMatrix(node, negateRotateAxis=True):
    if not isinstance(node, pm.PyNode):
        node = pm.PyNode(node)
    if isinstance(node, pm.nt.Transform):
        wm = pm.dt.TransformationMatrix(node.wm.get())
        if negateRotateAxis:
            r = pm.dt.EulerRotation(cmds.xform(
                node.longName(), q=True, ws=True, ro=True))
            wm.setRotation(r, node.getRotationOrder())
        return wm
    else:
        return pm.dt.TransformationMatrix()


def setWorldMatrix(node, matrix, translate=True, rotate=True, scale=True, matchAxes=False):
    """
    Args:
        node:
        matrix:
        translate:
        rotate:
        scale:
        matchAxes: TODO: document
    """
    if not isinstance(node, pm.PyNode):
        node = pm.PyNode(node)

    if not isinstance(matrix, pm.dt.TransformationMatrix):
        matrix = pm.dt.TransformationMatrix(matrix)

    # Convert the rotation order
    ro = node.getRotationOrder()
    if ro != matrix.rotationOrder():
        matrix.reorderRotation(ro)

    if translate:
        cmds.xform(node.longName(), ws=True,
                   t=matrix.getTranslation('world'))
    if rotate:
        if matchAxes and any(node.ra.get()):
            # Get the source's rotation matrix
            source_rotMtx = pm.dt.TransformationMatrix(
                getEulerRotationFromMatrix(matrix).asMatrix())
            # Get the target transform's inverse rotation matrix
            target_invRaMtx = pm.dt.EulerRotation(
                node.ra.get()).asMatrix().inverse()
            # Multiply the source's rotation matrix by the inverse of the
            # target's rotation axis to get just the difference in rotation
            target_rotMtx = target_invRaMtx * source_rotMtx
            # Get the new rotation value as a Euler in the correct rotation order
            target_rotation = getEulerRotationFromMatrix(target_rotMtx)
            rotation = target_rotation.reorder(node.getRotationOrder())
            rotation.setDisplayUnit('degrees')
        else:
            rotation = getEulerRotationFromMatrix(matrix)
        cmds.xform(node.longName(), ws=True, ro=rotation)
    if scale:
        localScaleMatrix = matrix * node.pim.get()
        cmds.xform(node.longName(), s=localScaleMatrix.getScale('world'))


def matchWorldMatrix(leader, *followers):
    """
    Set the world matrix of one or more nodes to match a leader's world matrix.

    Args:
        leader: A transform
        followers: One or more transforms to update
    """
    m = getWorldMatrix(leader)
    # handle joint orientations
    p = pm.xform(leader, q=True, ws=True, rp=True)
    r = pm.xform(leader, q=True, ws=True, ro=True)
    for f in followers:
        setWorldMatrix(f, m)
        pm.xform(f, t=p, ws=True)
        pm.xform(f, ro=r, ws=True)


def getRelativeMatrix(node, baseNode):
    """
    Return the matrix of a node relative to a base node.

    Args:
        node (PyNode): The node to retrieve the matrix from
        baseNode (PyNode): The node to which the matrix will be relative
    """
    return node.wm.get() * baseNode.wm.get().inverse()


def setRelativeMatrix(node, matrix, baseNode):
    """
    Set the world matrix of a node, given a matrix that
    is relative to a different base node.

    Args:
        node (PyNode): The node to modify
        matrix (Matrix): A matrix relative to baseNode
        baseNode (PyNode): The node that the matrix is relative to
    """
    setWorldMatrix(node, matrix * baseNode.wm.get())


def getTranslationMidpoint(a, b):
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


def getScaleMatrix(matrix):
    """
    Return a matrix representing only the scale of a TransformationMatrix
    """
    s = pm.dt.TransformationMatrix(matrix).getScale('world')
    return pm.dt.Matrix((s[0], 0, 0), (0, s[1], 0), (0, 0, s[2]))


def getRotationMatrix(matrix):
    """
    Return a matrix representing only the rotation of a TransformationMatrix
    """
    return pm.dt.TransformationMatrix(matrix).euler.asMatrix()


def normalizeEulerRotations(node):
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


def getAxis(value):
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


def getAxisVector(axis, sign=1):
    """
    Return a vector for a signed axis
    """
    i = int(axis)
    v = [0, 0, 0]
    v[i] = 1 * (1 if sign >= 0 else -1)
    return tuple(v)


def getOtherAxes(value, includeW=False):
    """
    Return a list of all other axes other than the given axis.

    Args:
        includeW: A bool, when True, include the W axis
    """
    axis = getAxis(value)
    if axis is not None:
        skip = [axis.index] + ([] if includeW else [3])
        return [a for a in pm.dt.Vector.Axis.values() if a.index not in skip]


def getClosestAlignedAxis(matrix, axis=0):
    """
    Given a matrix, find and return the signed axis
    that is most aligned with a specific axis.

    Args:
        matrix: A transformation matrix
        axis: The axis to check against

    Returns (axis, sign)
    """
    bestVal = None
    bestAxis = None
    for a in range(3):
        val = matrix[a][axis]
        if bestVal is None or abs(val) > abs(bestVal):
            bestVal = val
            bestAxis = a
    return getAxis(bestAxis), 1 if bestVal >= 0 else -1


def getClosestAlignedAxes(matrix):
    """
    Given a matrix, find and return signed axes closest to
    the x, y, and z world axes.

    Args:
        matrix: A transformation matrix

    Returns ((axisX, signX), (axisY, signY), (axisZ, signZ))
    """
    x, signX = getClosestAlignedAxis(matrix, 0)
    y, signY = getClosestAlignedAxis(matrix, 1)
    z, signZ = getClosestAlignedAxis(matrix, 2)
    return (x, signX), (y, signY), (z, signZ)


def getClosestAlignedRelativeAxis(nodeA, nodeB, axis=0):
    """
    Return the signed axis of nodeA that is most aligned
    with an axis of nodeB

    Returns (axis, sign)
    """
    return getClosestAlignedAxis(nodeA.wm.get() * nodeB.wim.get(), axis)


def areNodesAligned(nodeA, nodeB):
    """
    Return True if nodeA and nodeB are roughly aligned, meaning
    their axes point mostly in the same directions.
    """
    signedAxes = getClosestAlignedAxes(nodeA.wm.get() * nodeB.wim.get())
    for i, (axis, sign) in enumerate(signedAxes):
        if i != axis or sign != 1:
            return False
    return True


# Node Coloring
# -------------

def getOverrideColor(node):
    """
    Return the override color of a node.

    Args:
        node (PyNode): A transform node

    Returns:
        The color (RGB tuple), or None if color is
        not overridden.
    """
    shapes = node.getChildren(s=True)
    for shape in shapes:
        if shape.overrideEnabled.get() and shape.overrideRGBColors.get():
            return shape.overrideColorRGB.get()


def setOverrideColor(node, color, skipEnableOverrides=False):
    """
    Set the override color of a node

    Args:
        node (PyNode): A transform node
        color (tuple of float): An RGB color, 0..1
        skipEnableOverrides (bool): If True, skip enabling the overrides,
            just set the color. Faster if overrides are already enabled.
    """
    shapes = node.getChildren(s=True)

    for shape in shapes:
        if not skipEnableOverrides:
            shape.overrideEnabled.set(True)
            shape.overrideRGBColors.set(True)

        shape.overrideColorRGB.set(color)


def disableColorOverride(node):
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
