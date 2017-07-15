
import pymel.core as pm


__all__ = [
    'convertScaleConstraintToWorldSpace',
    'createOffsetGroup',
    'getAllParents',
    'getAssemblies',
    'getParentNodes',
    'setConstraintLocked',
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
    pm.cmds.xform(offset.nodeName(), objectSpace=True,
        translation=[0,0,0],
        rotation=[0,0,0],
        scale=[1,1,1],
        shear=[0,0,0],
    )

    # with transforms now absorbed, move offset to be a sibling of the node
    offset.setParent(node.getParent())

    # now parent the node to the new offset, and reset its transform
    node.setParent(offset)
    pm.cmds.xform(node.nodeName(), objectSpace=True,
        translation=[0,0,0],
        rotation=[0,0,0],
        scale=[1,1,1],
        shear=[0,0,0],
        # reset rotate axis since it is now part
        # of the offset transform
        rotateAxis=[0,0,0],
    )

    return offset




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


