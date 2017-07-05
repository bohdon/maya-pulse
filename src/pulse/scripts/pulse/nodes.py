

__all__ = [
    'getAllParents',
    'getAssemblies',
    'getParentNodes',
]

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