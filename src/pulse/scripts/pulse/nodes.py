
import logging
import pymel.core as pm

from pulse.vendor.mayacoretools import preservedSelection


__all__ = [
    'areNodesAligned',
    'convertScaleConstraintToWorldSpace',
    'createOffsetForSelected',
    'createOffsetGroup',
    'freezePivot',
    'freezePivotsForHierarchy',
    'freezePivotsForSelectedHierarchies',
    'freezeScalesForHierarchy',
    'freezeScalesForSelectedHierarchies',
    'getAllParents',
    'getAssemblies',
    'getAxis',
    'getAxisVector',
    'getClosestAlignedAxes',
    'getClosestAlignedRelativeAxis',
    'getExpandedAttrNames',
    'getOtherAxes',
    'getParentNodes',
    'getRotationMatrix',
    'getScaleMatrix',
    'getTransformHierarchy',
    'getTranslationMidpoint',
    'getWorldMatrix',
    'matchWorldMatrix',
    'parentInOrder',
    'parentSelected',
    'parentSelectedInOrder',
    'setConstraintLocked',
    'setParent',
    'setTransformHierarchy',
    'setWorldMatrix',
]


LOG = logging.getLogger(__name__)


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
    if isinstance(node, basestring):
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
    result = []
    for n in nodes:
        if any([p in nodes for p in getAllParents(n)]):
            continue
        result.append(n)
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


def getTransformHierarchy(transform, includeParent=True):
    """
    Return a list of (parent, [children]) tuples for a transform
    and all of its descendents.

    Args:
        transform: A Transform node
        includeParent: A bool, when True, the relationship between
            the transform and its parent is included
    """
    result = []
    if includeParent:
        result.append((transform.getParent(), [transform]))

    descendents = transform.listRelatives(ad=True, type='transform')

    for t in [transform] + descendents:
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


def parentSelected():
    """
    Parent the selected nodes. Select a leader then followers.

    [A, B, C] -> A|B, A|C
    """
    sel = pm.selected()
    if len(sel) < 2:
        pm.warning('More that one node must be selected')
        return
    setParent(sel[1:], sel[0])
    pm.select(sel)


def parentInOrder(nodes):
    """
    Parent the given nodes to each other in order.
    Leaders then folowers, eg. [A, B, C] -> A|B|C

    Args:
        nodes: A list of nodes to parent to each other in order
    """
    if len(nodes) < 2:
        pm.warning("More than one node must be given")
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


def parentSelectedInOrder():
    """
    Parent the selected nodes to each other in order.
    Select from top of hierarchy downward, eg. [A, B, C] -> A|B|C
    """
    with preservedSelection() as sel:
        parentInOrder(sel[:])


# Node Creation
# -------------

def createOffsetGroup(node, name='{0}_offset'):
    """
    Create a group transform that is inserted as the new parent of
    a node. The group absorbs all relative transformations of the node
    so that the nodes local matrix becomes identity. This includes
    absorbing the rotate axis of the node.

    Args:
        node: A PyNode to create an offset for
        name: A string that can optionally be formatted with
            the name of the node being grouped
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

    return offset


def createOffsetForSelected():
    """
    Create an offset group for the selected nodes
    """
    pm.select([createOffsetGroup(s) for s in pm.selected(type='transform')])


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
        if not isinstance(attrOrValue, basestring):
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


# Transform Modification
# ----------------------

def freezeScalesForHierarchy(transform):
    """
    Freeze scales on a transform and all its descendants without affecting pivots.
    Does this by parenting all children to the world, freezing, then restoring the hierarchy.

    Args:
        transform: A Transform node
    """
    hierarchy = getTransformHierarchy(transform)
    children = transform.listRelatives(ad=True, type='transform')
    for c in children:
        c.setParent(None)
    for n in [transform] + children:
        pm.makeIdentity(n, t=False, r=False, s=True, n=False, apply=True)
    setTransformHierarchy(hierarchy)


def freezeScalesForSelectedHierarchies():
    """
    Freeze scales on the selected transforms and all their descendants.
    See `freezeScalesForHierarchy` for more details.
    """
    with preservedSelection() as sel:
        tops = getParentNodes(sel[:])
        for t in tops:
            freezeScalesForHierarchy(t)


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


def freezePivotsForSelectedHierarchies():
    with preservedSelection() as sel:
        for s in sel:
            freezePivotsForHierarchy(s)


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
            r = pm.dt.EulerRotation(pm.cmds.xform(
                node.longName(), q=True, ws=True, ro=True))
            wm.setRotation(r, node.getRotationOrder())
        return wm
    else:
        return pm.dt.TransformationMatrix()


def setWorldMatrix(node, matrix, translate=True, rotate=True, scale=True, matchAxes=False):
    if not isinstance(node, pm.PyNode):
        node = pm.PyNode(node)

    if not isinstance(matrix, pm.dt.TransformationMatrix):
        matrix = pm.dt.TransformationMatrix(matrix)

    # Conver the rotation order
    ro = node.getRotationOrder()
    if ro != matrix.rotationOrder():
        matrix.reorderRotation(ro)

    if translate:
        pm.cmds.xform(node.longName(), ws=True,
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
        pm.cmds.xform(node.longName(), ws=True, ro=rotation)
    if scale:
        localScaleMatrix = matrix * node.pim.get()
        pm.cmds.xform(node.longName(), s=localScaleMatrix.getScale('world'))


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
    elif isinstance(value, basestring):
        for k in pm.dt.Vector.Axis.keys():
            if k.startswith(value):
                return getattr(pm.dt.Vector.Axis, k)


def getAxisVector(axis, sign=1):
    """
    Return a vector for a signed axis
    """
    i = int(axis)
    v = [0, 0, 0]
    v[i] = 1 * cmp(sign, 0)
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
    return getAxis(bestAxis), cmp(bestVal, 0)


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
