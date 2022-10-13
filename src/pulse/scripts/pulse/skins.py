import logging

import maya.OpenMaya as api
import maya.OpenMayaAnim as apianim
import pymel.core as pm

from .vendor import pymetanode as meta

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


def getSkinsFromJoint(joint):
    """
    Return a list of skin clusters in which a joint is an influence

    Args:
        joint (PyNode): A joint node
    """
    return list(set(joint.outputs(t="skinCluster")))


def getMeshesFromSkin(skin):
    """
    Return the mesh connected to a skin cluster
    """
    return list(set(skin.outputGeometry.listConnections()))


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
        influences (list of PyNode): An optional list of known influences, if omitted
            will retrieve all the influences from the skin
        influencesAsStrings (bool): If true, return influences as strings
            instead of PyNode objects

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
                influence_value = influence.nodeName() if influencesAsStrings else influence
                weight = weightsPlug[i].asFloat()
                weights.append((influence_value, weight))

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
    infIdByNameMap = dict([(v.nodeName(), k) for k, v in influences.items()])

    # keep track of missing influences
    missingInfluences = set()

    for vertIndex, vertWeights in weights:
        weightsPlug = skin.weightList[vertIndex].weights.__apiobject__()
        # keep track of original logical indices, set values to 0 on unused
        currentInfIds = api.MIntArray()
        weightsPlug.getExistingArrayAttributeIndices(currentInfIds)

        usedInfIds = []
        for inf, weight in vertWeights:
            infId = infIdMap.get(inf, None)
            if infId is None:
                # try retrieving by name
                infId = infIdByNameMap.get(inf, None)

            if infId is None:
                missingInfluences.add(inf)
                continue

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


def getSkinWeightsMap(*skins):
    """
    Return a dict containing weights for multiple skin clusters

    Args:
        *skins (PyNode): One or more skin cluster nodes

    Returns:
        A dict of {skinName: weights} for all the skin clusters
    """
    skinWeights = {}
    for skin in skins:
        weights = getSkinWeights(skin)
        skinWeights[skin.nodeName()] = weights
    return skinWeights


def applySkinWeightsMap(skinWeights, *skins):
    """
    Set the skin weights for multiple skin clusters.

    Args:
        skinWeights (dict): A map of skin node names to weights data,
            as given by `getSkinWeights`
        *skins (PyNode): One or more skin cluster nodes
    """
    for skin in skins:
        weights = skinWeights.get(skin.nodeName(), None)
        if not weights:
            LOG.warning("Could not find weights for skin: {0}".format(skin))
            continue
        setSkinWeights(skin, weights)


def saveSkinWeightsToFile(filePath, *skins):
    """
    Save skin weights to a .weights file for one or more skin clusters.

    Args:
        filePath (str): A full path to the .weights file to write
        *skins (PyNode): One or more skin cluster nodes
    """
    pm.progressWindow(t='Saving Weights...', min=0, max=100, status=None)

    pm.progressWindow(e=True, progress=0)
    skinWeights = getSkinWeightsMap(*skins)

    pm.progressWindow(e=True, progress=80)
    skinWeightsStr = meta.encodeMetaData(skinWeights)

    pm.progressWindow(e=True, progress=90)
    with open(filePath, 'w') as fp:
        fp.write(skinWeightsStr)

    pm.progressWindow(endProgress=True)
    LOG.info(filePath)


def applySkinWeightsFromFile(filePath, *skins):
    """
    Load skin weights from a .weights file, and apply it to
    one or more skin clusters.

    Args:
        filePath (str): A full path to the .weights file to read
        *skins (PyNode): One or more skin cluster nodes
    """
    with open(filePath, 'r') as fp:
        content = fp.read()

    skinWeights = meta.decodeMetaData(content)
    applySkinWeightsMap(skinWeights, *skins)
