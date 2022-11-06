import logging
from typing import List

import maya.OpenMaya as api
import maya.OpenMayaAnim as apianim
import pymel.core as pm

from .vendor import pymetanode as meta

LOG = logging.getLogger(__name__)


def get_skin_from_mesh(mesh):
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
            LOG.warning("More than one skin cluster found on %s", mesh)
        return skins[0]


def get_skins_from_joint(joint):
    """
    Return a list of skin clusters in which a joint is an influence

    Args:
        joint (PyNode): A joint node
    """
    return list(set(joint.outputs(t="skinCluster")))


def get_meshes_from_skin(skin):
    """
    Return the mesh connected to a skin cluster
    """
    return list(set(skin.outputGeometry.listConnections()))


def get_skin_influences(skin):
    """
    Return all influences affecting a sking.

    Args:
        skin (PyNode): A skin cluster node

    Returns:
        A dictionary with influence index (id) as keys
        and influence nodes as values.
    """
    result = {}
    skin_fn = apianim.MFnSkinCluster(skin.__apimobject__())
    infl_paths = api.MDagPathArray()
    skin_fn.influenceObjects(infl_paths)

    for i in range(infl_paths.length()):
        influence = pm.PyNode(infl_paths[i].node())
        index = skin_fn.indexForInfluenceObject(infl_paths[i])
        result[index] = influence

    return result


def get_skin_weights(skin, indices=None, influences=None, influences_as_strings=True):
    """
    Return the vertex weights of a skin, optionally filtered to only
    a set of vertex indices or influences.

    Args:
        skin (PyNode): A skin cluster node
        indices (list of int): If given, only return weights for the vertices
            at these indices
        influences (list of PyNode): An optional list of known influences, if omitted
            will retrieve all the influences from the skin
        influences_as_strings (bool): If true, return influences as strings
            instead of PyNode objects

    Returns:
        A list of tuples representing each vertex and the weights for
        each influence.
            e.g. [(index, [(influence, weight), ...]), ...]
    """
    result = []
    if influences is None:
        influences = get_skin_influences(skin)

    inf_ids = api.MIntArray()
    weight_list_plug = skin.wl.__apiobject__()
    weight_list_plug.getExistingArrayAttributeIndices(inf_ids)

    for vert in inf_ids:
        if indices is not None and vert not in indices:
            continue

        weights = []
        weights_plug = skin.wl[vert].weights.__apiobject__()
        for i in range(weights_plug.numElements()):
            # get logical index which matches the indices of the influence list
            logical = weights_plug[i].logicalIndex()
            if logical in influences:
                influence = influences[logical]
                influence_value = influence.nodeName() if influences_as_strings else influence
                weight = weights_plug[i].asFloat()
                weights.append((influence_value, weight))

        result.append((vert, weights))

    return result


def set_skin_weights(skin, weights, prune=True):
    """
    Set the exact weights for a skin.

    Args:
        skin (PyNode): A skin cluster node
        weights (list): A list of vertex weights, as given by `get_skin_weights`
        prune (bool): If true, remove influences that have no weights
    """
    # make sure the weight data is equal in length to the indices,
    # or the current weight list of the skin cluster

    influences = get_skin_influences(skin)
    inf_id_map = dict([(v, k) for k, v in influences.items()])
    inf_id_by_name_map = dict([(v.nodeName(), k) for k, v in influences.items()])

    # keep track of missing influences
    missing_influences = set()

    for vertIndex, vertWeights in weights:
        weights_plug = skin.weightList[vertIndex].weights.__apiobject__()
        # keep track of original logical indices, set values to 0 on unused
        current_inf_ids = api.MIntArray()
        weights_plug.getExistingArrayAttributeIndices(current_inf_ids)

        used_inf_ids = []
        for inf, weight in vertWeights:
            inf_id = inf_id_map.get(inf, None)
            if inf_id is None:
                # try retrieving by name
                inf_id = inf_id_by_name_map.get(inf, None)

            if inf_id is None:
                missing_influences.add(inf)
                continue

            weights_plug.elementByLogicalIndex(inf_id).setFloat(weight)
            used_inf_ids.append(inf_id)

        # assign 0 to unused existing plugs
        for i in range(current_inf_ids.length()):
            inf_id = current_inf_ids[i]
            if inf_id not in used_inf_ids:
                weights_plug.elementByLogicalIndex(inf_id).setFloat(0)

    if prune:
        pm.skinPercent(skin, skin.getGeometry(), nrm=False, prw=0)

    for inf in missing_influences:
        meshes = skin.getGeometry()
        mesh = meshes[0] if meshes else None
        LOG.warning("Mesh %s is missing influence: %s ", mesh, inf)

    return missing_influences


def normalize_weights_data(weights):
    """
    Return a copy of the given weights data, with all
    weight values normalized such that the sum of all weights
    for any vertex is equal to 1.

    Args:
        weights (list): A list of vertex weights, as given by `get_skin_weights`
    """

    def normalize(wts):
        total = sum([w[1] for w in wts])
        if total > 0:
            scale = 1.0 / total
            norm_wts = [[i, w * scale] for i, w in wts]
            return norm_wts
        else:
            return wts

    weights_copy = []
    for i in range(len(weights)):
        vert, wts = weights[i]
        norm_wts = normalize(wts)
        weights_copy.append((vert, norm_wts))

    return weights_copy


def normalize_skin_weights(skin):
    """
    Normalize the weights of a skin manually be retrieving the weights,
    applying numerical normalization, then reapplying the new weights.
    """
    weights = get_skin_weights(skin)
    norm_weights = normalize_weights_data(weights)
    set_skin_weights(skin, norm_weights)


def get_skin_weights_map(*skins):
    """
    Return a dict containing weights for multiple skin clusters

    Args:
        *skins (PyNode): One or more skin cluster nodes

    Returns:
        A dict of {skinName: weights} for all the skin clusters
    """
    skin_weights = {}
    for skin in skins:
        weights = get_skin_weights(skin)
        skin_weights[skin.nodeName()] = weights
    return skin_weights


def apply_skin_weights_map(skin_weights, *skins: List[pm.nt.SkinCluster]):
    """
    Set the skin weights for multiple skin clusters.

    Args:
        skin_weights (dict): A map of skin node names to weights data,
            as given by `get_skin_weights`
        *skins (PyNode): One or more skin cluster nodes
    """
    for skin in skins:
        weights = skin_weights.get(skin.nodeName(), None)
        if not weights:
            LOG.warning("Could not find weights for skin: %s", skin)
            continue
        set_skin_weights(skin, weights)


def save_skin_weights_to_file(file_path, *skins):
    """
    Save skin weights to a .weights file for one or more skin clusters.

    Args:
        file_path (str): A full path to the .weights file to write
        *skins (PyNode): One or more skin cluster nodes
    """
    pm.progressWindow(t='Saving Weights...', min=0, max=100, status=None)

    pm.progressWindow(e=True, progress=0)
    skin_weights = get_skin_weights_map(*skins)

    pm.progressWindow(e=True, progress=80)
    skin_weights_str = meta.encodeMetaData(skin_weights)

    pm.progressWindow(e=True, progress=90)
    with open(file_path, 'w') as fp:
        fp.write(skin_weights_str)

    pm.progressWindow(endProgress=True)
    LOG.info(file_path)


def apply_skin_weights_from_file(file_path, *skins: List[pm.nt.SkinCluster]):
    """
    Load skin weights from a .weights file, and apply it to
    one or more skin clusters.

    Args:
        file_path (str): A full path to the .weights file to read
        *skins (PyNode): One or more skin cluster nodes
    """
    with open(file_path, 'r') as fp:
        content = fp.read()

    skin_weights = meta.decodeMetaData(content)
    apply_skin_weights_map(skin_weights, *skins)
