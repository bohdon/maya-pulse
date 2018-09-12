
import logging
import pymel.core as pm  # pylint: disable=E0401
import maya.OpenMaya as api  # pylint: disable=E0401
import maya.OpenMayaAnim as apianim  # pylint: disable=E0401

__all__ = [
    'getSkinFromMesh',
    'getSkinFromJoint',
    'getSkinInfluences',
    'getSkinWeights',
    'setSkinWeights',
    'normalizeWeightsData',
    'normalizeSkinWeights',
]

LOG = logging.getLogger(__name__)


def getSkinFromMesh(mesh):
    """
    Return the main skin node from a mesh.

    Args:
        mesh (PyNode): A mesh node
    """
    skins = []
    for node in mesh.history(pruneDagObjects=True, interestLevel=2):
        if isinstance(node, pm.nt.SkinCluster):
            skins.append(node)

    if skins:
        if len(skins) > 1:
            LOG.warning("More than one skin cluster found on {0}".format(mesh))
        return skins[0]


def getSkinFromJoint(joint):
    """
    Return a list of skin clusters in which a joint is an influence

    Args:
        joint (PyNode): A joint node
    """
    return list(set(joint.outputs(t="skinCluster")))


def getSkinInfluences(skin):
    """
    Return all influences affecting a sking.

    Args:
        skin (PyNode): A skin cluster node

    Returns:
        A dictionary with influence index (id) as keys
        and influence nodes as values.
    """
    result = {}
    skinFn = apianim.MFnSkinCluster(skin.__apimobject__())
    inflPaths = api.MDagPathArray()
    skinFn.influenceObjects(inflPaths)

    for i in range(inflPaths.length()):
        influence = pm.PyNode(inflPaths[i].node())
        index = skinFn.indexForInfluenceObject(inflPaths[i])
        result[index] = influence

    return result


def getSkinWeights(skin, indices=None, influences=None,
                   influencesAsStrings=True):
    """
    Return the vertex weights of a skin, optionally filtered to only
    a set of vertex indices or influences.

    Args:
        skin (PyNode): A skin cluster node
        indices (list of int): If given, only return weights for the vertices
            at these indices
        influences (?): ?
        influencesAsStrings (?): ?

    Returns:
        A list of tuples representing each vertex and the weights for
        each influence.
            e.g. [(index, [(influence, weight), ...]), ...]
    """
    result = []
    if influences is None:
        influences = getSkinInfluences(skin)

    infIds = api.MIntArray()
    weightListPlug = skin.wl.__apiobject__()
    weightListPlug.getExistingArrayAttributeIndices(infIds)

    for vert in infIds:
        if indices is not None and vert not in indices:
            continue

        weights = []
        weightsPlug = skin.wl[vert].weights.__apiobject__()
        for i in range(weightsPlug.numElements()):
            # get logical index which matches the indices of the influence list
            logical = weightsPlug[i].logicalIndex()
            if logical in influences:
                influence = influences[logical]
                weight = weightsPlug[i].asFloat()
                weights.append((influence, weight))

        result.append((vert, weights))

    return result


def setSkinWeights(skin, weights, prune=True):
    """
    Set the exact weights for a skin.

    Args:
        skin (PyNode): A skin cluster node
        weights (list): A list of vertex weights, as given by `getSkinWeights`
        prune (bool): If true, remove influences that have no weights
    """
    # make sure the weight data is equal in length to the indices,
    # or the current weight list of the skin cluster

    influences = getSkinInfluences(skin)
    infIdMap = dict([(v, k) for k, v in influences.items()])

    # keep track of missing influences
    missingInfluences = set()

    for vertIndex, vertWeights in weights:
        weightsPlug = skin.weightList[vertIndex].weights.__apiobject__()
        # keep track of original logical indices, set values to 0 on unused
        currentInfIds = api.MIntArray()
        weightsPlug.getExistingArrayAttributeIndices(currentInfIds)

        usedInfIds = []
        for inf, weight in vertWeights:
            if inf not in infIdMap:
                missingInfluences.add(inf)
                continue

            infId = infIdMap[inf]
            weightsPlug.elementByLogicalIndex(infId).setFloat(weight)
            usedInfIds.append(infId)

        # assign 0 to unused existing plugs
        for i in range(currentInfIds.length()):
            infId = currentInfIds[i]
            if infId not in usedInfIds:
                weightsPlug.elementByLogicalIndex(infId).setFloat(0)

    if prune:
        pm.skinPercent(skin, skin.getGeometry(), nrm=False, prw=0)

    for inf in missingInfluences:
        meshes = skin.getGeometry()
        mesh = meshes[0] if meshes else None
        LOG.warning("Mesh {0} is missing influence: {1} ".format(mesh, inf))

    return missingInfluences


def normalizeWeightsData(weights):
    """
    Return a copy of the given weights data, with all
    weight values normalized such that the sum of all weights
    for any vertex is equal to 1.

    Args:
        weights (list): A list of vertex weights, as given by `getSkinWeights`
    """
    def normalize(wts):
        total = sum([w[1] for w in wts])
        if total > 0:
            scale = 1.0 / total
            normWts = [[i, w * scale] for i, w in wts]
            return normWts
        else:
            return wts

    weightsCopy = []
    for i in range(len(weights)):
        vert, wts = weights[i]
        normWts = normalize(wts)
        weightsCopy.append((vert, normWts))

    return weightsCopy


def normalizeSkinWeights(skin):
    """
    Normalize the weights of a skin manually be retrieving the weights,
    applying numerical normalization, then reapplying the new weights.
    """
    weights = getSkinWeights(skin)
    normWeights = normalizeWeightsData(weights)
    setSkinWeights(skin, normWeights)
