import logging
import re
from typing import List

import maya.OpenMaya as api
import maya.OpenMayaAnim as apianim
import pymel.core as pm
from maya import cmds

from .vendor import pymetanode as meta
from .vendor.mayacoretools import preserved_selection

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


def move_inf_weights_to_parents(weights, inf_pattern):
    """
    Find influences by pattern, and move their weights to the first parent not removed.

    Return:
        A tuple of (new_weights, changed) where changed is true if any influences were remapped.
    """
    pat = re.compile(inf_pattern)
    inf_parent_map = {}

    def get_new_inf(inf: str) -> str:
        """
        Return the influence to use for a given influence, remapping
        to it's parent if this influence will be removed.
        """
        if not pat.match(inf):
            return inf

        # check cached map
        if inf in inf_parent_map:
            return inf_parent_map[inf]

        parent = inf
        while True:
            parent = cmds.listRelatives(parent, parent=True)
            if not parent:
                break
            parent = parent[0]

            # use the parent (if it won't also be removed)
            if not pat.match(parent):
                return parent

        # no valid parent, skip removal
        return inf

    def combine_vert_weights(_vert_weights: list[tuple[str, float]]):
        new_wts_map = {}
        changed = False
        for inf, weight in _vert_weights:
            new_inf = get_new_inf(inf)

            if inf != new_inf:
                changed = True
                # log the first remap
                if inf not in inf_parent_map:
                    LOG.info(f"Replacing {inf} with {new_inf}")
                    inf_parent_map[inf] = new_inf

            if new_inf in new_wts_map:
                # combine with existing influence
                new_wts_map[new_inf] += weight
            else:
                # add new influence
                new_wts_map[new_inf] = weight

        # clamp or round weights that are nearly 1
        _result = []
        for inf, new_weight in new_wts_map.items():
            if abs(new_weight) < 0.0001:
                # prune
                continue
            elif abs(1.0 - new_weight) < 0.0001:
                new_weight = 1.0
            _result.append((inf, new_weight))

        return _result, changed

    result = []
    did_any_change = False
    for vert_idx, vert_weights in weights:
        new_vert_weights, did_change = combine_vert_weights(vert_weights)
        did_any_change |= did_change

        result.append((vert_idx, new_vert_weights))

    return result, did_any_change


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
    pm.progressWindow(t="Saving Weights...", min=0, max=100, status=None)

    pm.progressWindow(e=True, progress=0)
    skin_weights = get_skin_weights_map(*skins)

    pm.progressWindow(e=True, progress=80)
    skin_weights_str = meta.encode_metadata(skin_weights)

    pm.progressWindow(e=True, progress=90)
    with open(file_path, "w") as fp:
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
    with open(file_path, "r") as fp:
        content = fp.read()

    skin_weights = meta.decode_metadata(content)
    apply_skin_weights_map(skin_weights, *skins)


def smooth_mesh_border_normals(meshes, merge_threshold=0.001):
    """
    Fix seams along the borders of adjacent meshes by combining, smoothing, and transferring
    normals back to the original meshes. Affects all normals touching the border faces, but
    makes sure only the border vertex normals remain locked.
    """
    with preserved_selection():
        dupes = pm.duplicate(meshes)
        combined = pm.polyUnite(dupes, constructionHistory=False)
        pm.polyMergeVertex(distance=merge_threshold, constructionHistory=False)
        pm.polySoftEdge(angle=360, constructionHistory=False)

        for mesh in meshes:
            pm.select(mesh.faces)
            pm.polySelectConstraint(border=True, mode=2)
            pm.polySelectConstraint(border=False, mode=0)

            # copy normals on border faces (affects two rows of vertices)
            pm.transferAttributes(
                combined,
                pm.selected(),
                transferPositions=False,
                transferNormals=True,
                transferUVs=False,
                transferColors=False,
                sampleSpace=3,
                searchMethod=3,
            )
            pm.delete(mesh, constructionHistory=True)

            # unfreeze non-border vertex normals (unlock the non-border row)
            pm.mel.ConvertSelectionToVertices()
            border_vts = pm.polySelectConstraint(border=True, mode=2, returnSelection=True)
            pm.polySelectConstraint(border=False, mode=0)
            pm.select(border_vts, deselect=True)
            pm.polyNormalPerVertex(pm.selected(), unFreezeNormal=True)

            # and smooth the non-border edges as well
            pm.mel.ConvertSelectionToContainedEdges()
            pm.polySoftEdge(angle=360, constructionHistory=False)

        pm.delete(combined)
