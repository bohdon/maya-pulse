"""
A function library of miscellaneous utils usually involving
editor selection or interactive work. Many UI commands are
located here, as they can be more specific than the core api
but still not dependent on a UI.
"""

import os
import logging
import maya.cmds as cmds
import pymel.core as pm

from pulse.vendor.mayacoretools import preservedSelection

from pulse.colors import *
from pulse.joints import *
from pulse.nodes import *
from pulse.shapes import *
from pulse.sym import *
import pulse.links
import pulse.skins

__all__ = [
    'centerSelectedJoints',
    'createOffsetForSelected',
    'disableColorOverrideForSelected',
    'disableSegmentScaleCompensateForSelected',
    'freezeOffsetMatricesForSelectedHierarchies',
    'freezePivotsForSelectedHierarchies',
    'freezeScalesForSelectedHierarchies',
    'getDetailedChannelBoxAttrs',
    'getNamedColor',
    'getSelectedTransforms',
    'insertJointForSelected',
    'isDetailedChannelBoxEnabled',
    'linkSelected',
    'mirrorSelected',
    'orientToJointForSelected',
    'orientToWorldForSelected',
    'pairSelected',
    'parentSelected',
    'parentSelectedInOrder',
    'rotateSelectedComponentsAroundAxis',
    'rotateSelectedOrientsAroundAxis',
    'saveSceneIfDirty',
    'saveSkinWeightsForSelected',
    'setDetailedChannelBoxEnabled',
    'setOverrideColorForSelected',
    'snapToLinkForSelected',
    'toggleDetailedChannelBoxForSelected',
    'toggleLocalRotationAxesForSelected',
    'unfreezeOffsetMatricesForSelectedHierarchies',
    'unlinkSelected',
    'unpairSelected',
]

LOG = logging.getLogger(__name__)


def saveSceneIfDirty(prompt=True):
    """
    Prompt the user to save if the scene is modified, or has never been saved.

    Returns True if the save was successful, or the scene has not been modified.

    Args:
        prompt (bool): If True, prompt the user, or attempt to automatically save where possible
    """
    modified = pm.cmds.file(q=True, modified=True)
    neverSaved = not pm.sceneName()

    if neverSaved:
        # first time saving
        if not prompt:
            pm.runtime.SaveSceneAs()
            return bool(pm.sceneName())
        else:
            # either save as or cancel
            kwargs = dict(
                title='Warning: Scene Not Saved',
                message='Save changes to untitled scene?',
                db="Save", cb="Cancel", ds="Cancel",
                button=("Save", "Cancel"),
            )
            result = pm.confirmDialog(**kwargs)
            if result == 'Save':
                pm.runtime.SaveSceneAs()
                return bool(pm.sceneName())
            else:
                return False

    elif modified:
        # saving modified file
        if not prompt:
            return pm.saveFile(force=True)
        else:
            kwargs = dict(
                title='Save Scene',
                message='Save changes to\n{0}'.format(pm.sceneName()),
                db="Save", cb="Cancel", ds="Cancel",
                button=("Save", "Cancel"),
            )
            result = pm.confirmDialog(**kwargs)
            if result == 'Save':
                return pm.saveFile(force=True)
            else:
                return False

    else:
        return True


def getEditorBlueprint():
    """
    Return the shared Blueprint instance from the default UI model
    """
    import pulse.views
    return pulse.views.BlueprintUIModel.getDefaultModel().blueprint


def getSelectedTransforms(includeChildren=False):
    """
    Return the currently selected transforms (or joints).

    Args:
        includeChildren (bool): If true, also include all descendants
            if the selected nodes
    """
    sel = pm.selected(type=['transform', 'joint'])
    if includeChildren:
        result = []
        for s in sel:
            if s not in result:
                result.append(s)
            for child in s.listRelatives(ad=True, type=['transform', 'joint']):
                if child not in result:
                    result.append(child)
        return result
    else:
        return sel


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


def insertJointForSelected(count=1):
    """
    Insert joints above the selected joint
    """
    result = []
    for s in pm.selected():
        result.extend(insertJoints(s, count))
    pm.select(result)


def createOffsetForSelected():
    """
    Create an offset group for the selected nodes
    """
    pm.select([createOffsetGroup(s) for s in pm.selected(type='transform')])


def freezeScalesForSelectedHierarchies():
    """
    Freeze scales on the selected transforms and all their descendants.
    See `freezeScalesForHierarchy` for more details.
    """
    with preservedSelection() as sel:
        tops = getParentNodes(sel[:])
        for t in tops:
            freezeScalesForHierarchy(t)


def freezePivotsForSelectedHierarchies():
    with preservedSelection() as sel:
        for s in sel:
            freezePivotsForHierarchy(s)


def freezeOffsetMatricesForSelectedHierarchies():
    with preservedSelection() as sel:
        for s in sel:
            freezeOffsetMatrixForHierarchy(s)


def unfreezeOffsetMatricesForSelectedHierarchies():
    with preservedSelection() as sel:
        for s in sel:
            unfreezeOffsetMatrixForHierarchy(s)


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


def parentSelectedInOrder():
    """
    Parent the selected nodes to each other in order.
    Select from top of hierarchy downward, eg. [A, B, C] -> A|B|C
    """
    with preservedSelection() as sel:
        parentInOrder(sel[:])


def rotateSelectedComponentsAroundAxis(axis, degrees=90):
    """
    Rotate the components of a shape by 90 degrees along one axis

    Args:
        axis: A int representing which axis to rotate around
            X = 0, Y = 1, Z = 2
        degrees: A float, how many degrees to rotate the components on that axis
            default is 90
    """
    rotation = pm.dt.Vector()
    rotation[axis] = degrees
    for node in pm.selected():
        for shape in node.getShapes():
            rotateComponents(shape, rotation)


def orientToWorldForSelected(
        includeChildren=False,
        preserveChildren=True,
        preserveShapes=True,
        syncJointAxes=True):
    """
    Orient the selected joints or transforms to match
    the world aligned axes
    """
    # TODO: implement preserveShapes
    sel = getSelectedTransforms(includeChildren)
    for node in sel:
        if node.nodeType() == 'joint':
            orientJointToWorld(node)
            if syncJointAxes:
                matchJointRotationToOrient(node, preserveChildren)
        else:
            pm.rotate(node, (0, 0, 0), a=True, ws=True, pcp=preserveChildren)


def orientToJointForSelected(
        axisOrder,
        upAxisStr,
        includeChildren=False,
        preserveChildren=True,
        preserveShapes=True,
        syncJointAxes=True):
    """
    """
    sel = getSelectedTransforms(includeChildren)
    for node in sel:
        if node.nodeType() == 'joint':
            orientJoint(node, axisOrder, upAxisStr)
            # if syncJointAxes:
            #     matchJointRotationToOrient(node, preserveChildren)


def rotateSelectedOrientsAroundAxis(
        axis, degrees=90,
        preserveChildren=True,
        preserveShapes=True,
        syncJointAxes=True):
    """
    Rotate the selected nodes around the given axis
    If the node is a joint, its jointOrient will be rotated

    Args:
        axis:
        degress:
        preserveChildren:
        preserveShapes:
        syncJointAxes (bool): If True, joints will also have their
            translate and scale axes updated to match the new orientation
    """
    # if currently on move tool, make sure its object space
    if pm.currentCtx() == pm.melGlobals['$gMove']:
        pm.manipMoveContext('Move', e=True, mode=0)

    rotation = pm.dt.Vector()
    rotation[axis] = degrees

    nodes = pm.selected()
    for node in nodes:
        rotateOrientOrTransform(
            node, rotation,
            preserveChildren, preserveShapes, syncJointAxes)


def rotateOrientOrTransform(
        node, rotation,
        preserveChildren=True,
        preserveShapes=True,
        syncJointAxes=True):
    """
    Rotate a node in local space, or if its a joint, by
    modifying the joint orient. Additionally, can preserve
    child transform positions and/or shapes (such as control cvs).

    Args:
        node:
        rotation:
        preserveChildren:
        preserveShapes:
        syncJointAxes (bool): If True, joints will also have their
            translate and scale axes updated to match the new orientation
    """
    if node.nodeType() == 'joint':
        rotateJointOrient(node, rotation)
        if syncJointAxes:
            matchJointRotationToOrient(node, preserveChildren)
    else:
        pm.rotate(node, rotation, os=True, r=True, pcp=preserveChildren)

        # normalize eulers to 0..360, assumed as part of orienting
        normalizeEulerRotations(node)

        if preserveShapes:
            shapes = node.getShapes()
            for shape in shapes:
                rotateComponents(shape, -rotation)


def matchJointRotationToOrientForSelected(preserveChildren=True):
    sel = pm.selected(type='joint')
    for node in sel:
        matchJointRotationToOrient(node, preserveChildren)


def getDetailedChannelBoxAttrs(node):
    """
    Return the list of attributes that are included
    when the 'detailed channel box' is enabled for a node.
    """
    attrs = [
        # rotate order
        'ro',
        # rotate axis
        'rax', 'ray', 'raz',
        # rotate pivot
        'rpx', 'rpy', 'rpz',
        # scale pivot
        'spx', 'spy', 'spz',
        # rotate pivot translate
        'rptx', 'rpty', 'rptz',
        # scale pivot translate
        'sptx', 'spty', 'sptz',
    ]

    if node.nodeType() == 'joint':
        attrs += [
            # joint orient
            'jox', 'joy', 'joz',
        ]

    return attrs


def isDetailedChannelBoxEnabled(node):
    def isVisibleInCB(node, attr):
        return cmds.getAttr(node + '.' + attr, cb=True)

    attrs = getDetailedChannelBoxAttrs(node)
    if any([isVisibleInCB(node, a) for a in attrs]):
        return True


def setDetailedChannelBoxEnabled(node, enabled=True):
    """
    Set whether a node should display detailed channel box
    attributes related to transforms and joint orients.
    """
    attrs = getDetailedChannelBoxAttrs(node)
    for attr in attrs:
        pm.cmds.setAttr(node + '.' + attr, cb=enabled)


def toggleDetailedChannelBoxForSelected():
    """
    Toggle the display of detailed channel box attributes
    for all selected nodes.
    """
    sel = pm.selected()

    isEnabled = False
    for s in sel:
        if isDetailedChannelBoxEnabled(s):
            isEnabled = True
            break

    for s in sel:
        setDetailedChannelBoxEnabled(s, not isEnabled)


def toggleLocalRotationAxesForSelected(includeChildren=False):
    sel = getSelectedTransforms(includeChildren)
    isEnabled = False
    for s in sel:
        if s.dla.get():
            isEnabled = True
            break

    for s in sel:
        s.dla.set(not isEnabled)


def linkSelected():
    sel = pm.selected()
    if len(sel) != 2:
        LOG.warning("Select a leader then a follower")
        return

    pulse.links.link(sel[0], sel[1])


def unlinkSelected():
    for s in pm.selected():
        pulse.links.unlink(s)


def snapToLinkForSelected():
    sel = pm.selected()
    if not sel:
        sel = pulse.links.getAllLinkedNodes()
        # TODO: sort by parenting hierarchy

    for node in sel:
        pulse.links.snapToLink(node)


def pairSelected():
    sel = pm.selected()
    if len(sel) == 2:
        pairMirrorNodes(sel[0], sel[1])


def unpairSelected():
    for s in pm.selected():
        unpairMirrorNode(s)


def mirrorSelected(
        recursive=True,
        create=True,
        curveShapes=True,
        links=True,
        reparent=True,
        transform=True,
        appearance=True):
    """
    Perform a mirroring operation on the selected nodes.

    Args:
        recursive (bool): Mirror the selected nodes and all children
        create (bool): Allow creation of new nodes if a pair is not found
        curveShapes (bool): Flip curve shapes of newly created nodes
        links (bool): Mirror links. See links.py
        reparent (bool): Mirror the parenting structure of the nodes
        transform (bool): Mirror the transform matrices of the nodes
        appearance (bool): Mirror the name and color of the nodes
    """
    nodes = pm.selected()
    if not nodes:
        LOG.warning("Select at least one node to mirror")
        return

    util = MirrorUtil()
    util.isRecursive = recursive
    util.isCreationAllowed = create

    if curveShapes:
        util.addOperation(MirrorCurveShapes())
    if links:
        util.addOperation(MirrorLinks())
    if reparent:
        util.addOperation(MirrorParenting())
    if transform:
        # TODO: configure the transform util with mirror mode, etc
        util.addOperation(MirrorTransforms())
    if appearance:
        blueprint = getEditorBlueprint()
        if blueprint:
            namesOp = MirrorNames()
            namesOp.blueprint = blueprint
            util.addOperation(namesOp)
            colorsOp = MirrorColors()
            colorsOp.blueprint = blueprint
            util.addOperation(colorsOp)

    util.run(nodes)


def saveSkinWeightsForSelected(filePath=None):
    """
    Save skin weights for the selected meshes to a file.

    Args:
        filePath (str): A full path to a .weights file to write. If None,
            will use the scene name.
    """
    if filePath is None:
        sceneName = pm.sceneName()
        if not sceneName:
            LOG.warning("Scene is not saved")
            return
        filePath = os.path.splitext(sceneName)[0] + '.weights'

    skins = [pulse.skins.getSkinFromMesh(m) for m in pm.selected()]
    skins = [s for s in skins if s]

    pulse.skins.saveSkinWeightsToFile(filePath, *skins)


def getNamedColor(name):
    """
    Return a color by name from the config of the editor Blueprint
    """
    blueprint = getEditorBlueprint()
    if blueprint:
        config = blueprint.getConfig()
        for color in config.get('colors', []):
            if color.get('name') == name:
                color = color.get('color')
                if color:
                    return colors.hexToRGB01(color)


def setOverrideColorForSelected(color):
    """
    Set the display override color for the selected nodes
    """
    for node in pm.selected():
        pulse.nodes.setOverrideColor(node, color)


def disableColorOverrideForSelected():
    for node in pm.selected():
        pulse.nodes.disableColorOverride(node)
