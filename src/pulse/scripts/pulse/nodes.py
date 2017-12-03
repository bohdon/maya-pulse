
import pymel.core as pm

from mayacoretools import preservedSelection


__all__ = [
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
    'getExpandedAttrNames',
    'getParentNodes',
    'getTransformHierarchy',
    'parentInOrder',
    'parentSelected',
    'parentSelectedInOrder',
    'setConstraintLocked',
    'setParent',
    'setTransformHierarchy',
]


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
    return list(set([n[:(n+'|').find('|', 1)] for n in nodes]))



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
        parent, child = nodes[i:i+2]
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
        translation=[0,0,0],
        rotation=[0,0,0],
        scale=[1,1,1],
        shear=[0,0,0],
    )

    # with transforms now absorbed, move offset to be a sibling of the node
    offset.setParent(node.getParent())

    # now parent the node to the new offset, and reset its transform
    node.setParent(offset)
    pm.xform(node, objectSpace=True,
        translation=[0,0,0],
        rotation=[0,0,0],
        scale=[1,1,1],
        shear=[0,0,0],
        # reset rotate axis since it is now part
        # of the offset transform
        rotateAxis=[0,0,0],
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
        attrs: A list of strings representing attribute names
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
            attrs.extend(['target[%d].targetOffsetTranslate%s' % (i, a) for a in 'XYZ'])
            attrs.extend(['target[%d].targetOffsetRotate%s' % (i, a) for a in 'XYZ'])
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
    translate = pm.dt.Vector(pm.xform(transform, q=True, t=True, worldSpace=True))
    parentTranslate = pm.dt.Vector()
    parent = transform.getParent()
    if parent:
        # we want the world space matrix translate of the parent
        # because thats the real location that zeroed out child transforms would exist.
        # note that the world space translate (not retrieving matrix) can be a different value
        parentTranslate = pm.dt.Matrix(pm.xform(parent, q=True, m=True, worldSpace=True)).translate
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
