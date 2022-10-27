"""
A function library of miscellaneous utils usually involving
editor selection or interactive work. Many UI commands are
located here, as they can be more specific than the core api
but still not dependent on a UI.
"""

import logging
import os
from typing import Optional

import maya.cmds as cmds
import pymel.core as pm

from . import joints
from . import links
from . import nodes
from . import shapes
from . import skins
from . import sym
from . import sourceeditor
from .colors import LinearColor
from .vendor.mayacoretools import preservedSelection

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
    from .ui.core import BlueprintUIModel
    return BlueprintUIModel.getDefaultModel().blueprint


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
        joints.centerJoint(s)


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
        result.extend(joints.insertJoints(s, count))
    pm.select(result)


def createOffsetForSelected():
    """
    Create an offset group for the selected nodes
    """
    pm.select([nodes.createOffsetTransform(s)
               for s in pm.selected(type='transform')])


def freezeScalesForSelectedHierarchies(skipJoints=True):
    """
    Freeze scales on the selected transforms and all their descendants.
    See `freezeScalesForHierarchy` for more details.

    Args:
        skipJoints (bool): If true, don't attempt to freeze joint hierarchies. Does not prevent
            freezing joints if they are a child of one of the selected transforms.
    """
    with preservedSelection() as sel:
        topNodes = nodes.getParentNodes(sel[:])
        for topNode in topNodes:
            if not skipJoints or topNode.nodeType() != 'joint':
                nodes.freezeScalesForHierarchy(topNode)


def freezePivotsForSelectedHierarchies():
    with preservedSelection() as sel:
        for s in sel:
            nodes.freezePivotsForHierarchy(s)


def freezeOffsetMatricesForSelectedHierarchies():
    with preservedSelection() as sel:
        for s in sel:
            nodes.freezeOffsetMatrixForHierarchy(s)


def unfreezeOffsetMatricesForSelectedHierarchies():
    with preservedSelection() as sel:
        for s in sel:
            nodes.unfreezeOffsetMatrixForHierarchy(s)


def freezeJointsForSelectedHierarchies():
    """
    Freeze rotates and scales on the selected joint hierarchies.
    """
    with preservedSelection() as sel:
        topNodes = nodes.getParentNodes(sel[:])
        for topNode in topNodes:
            if topNode.nodeType() == 'joint':
                joints.freezeJoints(topNode)


def parentSelected():
    """
    Parent the selected nodes. Select a leader then followers.

    [A, B, C] -> A|B, A|C
    """
    sel = pm.selected()
    if len(sel) < 2:
        pm.warning('More that one node must be selected')
        return
    nodes.setParent(sel[1:], sel[0])
    pm.select(sel)


def parentSelectedInOrder():
    """
    Parent the selected nodes to each other in order.
    Select from top of hierarchy downward, eg. [A, B, C] -> A|B|C
    """
    with preservedSelection() as sel:
        nodes.parentInOrder(sel[:])


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
            shapes.rotate_components(shape, rotation)


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
            joints.orientJointToWorld(node)
            if syncJointAxes:
                joints.matchJointRotationToOrient(node, preserveChildren)
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
            joints.orientJoint(node, axisOrder, upAxisStr)
            # if syncJointAxes:
            #     matchJointRotationToOrient(node, preserveChildren)


def orientToParentForSelected(includeChildren=False, preserveChildren=True):
    """
    """
    sel = getSelectedTransforms(includeChildren)
    for node in sel:
        if node.nodeType() == 'joint':
            joints.orientJointToParent(node, preserveChildren)


def orientIKJointsForSelected(aimAxis="x", poleAxis="y", preserveChildren=True):
    sel = pm.selected(type='joint')
    for node in sel:
        joints.orientIKJoints(node, aimAxis=aimAxis, poleAxis=poleAxis,
                              preserveChildren=preserveChildren)


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

    sel_nodes = pm.selected()
    for node in sel_nodes:
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
        joints.rotateJointOrient(node, rotation)
        if syncJointAxes:
            joints.matchJointRotationToOrient(node, preserveChildren)
    else:
        pm.rotate(node, rotation, os=True, r=True, pcp=preserveChildren)

        # normalize eulers to 0..360, assumed as part of orienting
        nodes.normalizeEulerRotations(node)

        if preserveShapes:
            nodeShapes = node.getShapes()
            for shape in nodeShapes:
                shapes.rotate_components(shape, -rotation)


def orientJointToRotationForSelected(includeChildren=False, preserveChildren=True):
    sel_nodes = getSelectedTransforms(includeChildren)
    for node in sel_nodes:
        if node.nodeType() == 'joint':
            joint = node.node()
            joints.orientJointToRotation(joint, preserveChildren)


def interactiveOrientForSelected():
    sel = pm.selected(type='joint')
    rotateAxes = [s.rotateAxis for s in sel]
    pm.select(rotateAxes)


def fixupJointOrientForSelected(aimAxis="x", keepAxis="y", preserveChildren=True):
    sel = pm.selected(type='joint')
    for node in sel:
        joints.fixupJointOrient(node, aimAxis=aimAxis, keepAxis=keepAxis,
                                preserveChildren=preserveChildren)


def matchJointRotationToOrientForSelected(preserveChildren=True):
    # handle current selection containing both joints, and possibly pivots of joints
    sel = pm.selected()
    for s in sel:
        if s.nodeType() == 'joint':
            joint = s.node()
            joints.matchJointRotationToOrient(joint, preserveChildren)


def markEndJointsForSelected():
    """
    Find all end joints, and rename them to END_jnt, and set their override colors
    Returns:

    """
    sel = pm.selected()
    for s in sel:
        end_joints = joints.getEndJoints(s)
        for end_joint in end_joints:
            end_joint.rename('END_jnt')
            end_joint.overrideEnabled.set(True)
            end_joint.overrideRGBColors.set(True)
            end_joint.overrideColorRGB.set((0.35, 0, 0))


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


def linkSelected(linkType=links.LinkType.DEFAULT, keepOffset=False):
    sel = pm.selected()
    if len(sel) < 2:
        LOG.warning("Select at least one leader, then a follower last")
        return

    positioner = links.getPositioner(linkType)
    positioner.keepOffset = keepOffset
    follower = sel[-1]
    leaders = sel[:-1]
    positioner.createLink(follower, leaders)


def linkSelectedWeighted(keepOffset=False):
    sel = pm.selected()
    if len(sel) < 2:
        LOG.warning("Select at least one leader, then a follower last")
        return

    positioner = links.getPositioner(links.LinkType.WEIGHTED)
    positioner.keepOffset = keepOffset
    follower = sel[-1]
    leaders = sel[:-1]
    positioner.weights = [1] * len(leaders)
    positioner.createLink(follower, leaders)


def unlinkSelected():
    for s in pm.selected():
        links.unlink(s)


def recreateLinksForSelected(keepOffset=False):
    for s in pm.selected():
        links.recreateLink(s, keepOffset=keepOffset)


def upgradeAllLinks():
    """
    Update all links in the scene, fixing up old data as necessary.
    """
    for n in pm.ls():
        linkData = links.getLinkMetaData(n)
        if linkData:
            changed = False

            # support legacy data of just a target node, not a dict
            if isinstance(linkData, pm.PyNode):
                linkData = {'targetNodes': [linkData]}
                changed = True

            # ensure link type key exists
            if 'type' not in linkData:
                linkData['type'] = links.LinkType.DEFAULT
                changed = True

            # upgrade targetNode (single target) to targetNodes (list of targets)
            if 'targetNode' in linkData:
                targetNode = linkData['targetNode']
                del linkData['targetNode']
                linkData['targetNodes'] = [targetNode]
                changed = True

            if changed:
                LOG.info('Updated link data for %s', n)
                links.setLinkMetaData(n, linkData)


def positionLinkForSelected():
    sel = pm.selected()
    if not sel:
        sel = links.getAllLinkedNodes()
        # TODO: sort by parenting hierarchy
    else:
        oldLen = len(sel)
        # filter for only linked nodes
        sel = [s for s in sel if links.isLinked(s)]
        if oldLen > 0 and len(sel) == 0:
            # something was selected, but no linked nodes
            LOG.warning("No linked nodes were selected")

    showProgress = (len(sel) > 20)
    if showProgress:
        pm.progressWindow(t='Positioning Links', min=0, max=len(sel))
    for node in sel:
        links.applyLinkPosition(node)
        if showProgress:
            pm.progressWindow(e=True, step=1)
    if showProgress:
        pm.progressWindow(endProgress=True)


def pairSelected():
    sel = pm.selected()
    if len(sel) == 2:
        sym.pair_mirror_nodes(sel[0], sel[1])


def unpairSelected():
    for s in pm.selected():
        sym.unpair_mirror_node(s)


def mirrorSelected(recursive=True, create=True, curveShapes=True, links=True,
                   reparent=True, transform=True, appearance=True):
    """
    Perform a mirroring operation on the selected nodes.

    Args:
        recursive (bool): Mirror the selected nodes and all children
        create (bool): Allow creation of new nodes if a pair is not found
        curveShapes (bool): Mirror control shape curves
        links (bool): Mirror links. See links.py
        reparent (bool): Mirror the parenting structure of the nodes
        transform (bool): Mirror the transform matrices of the nodes
        appearance (bool): Mirror the name and color of the nodes
    """
    sel_nodes = pm.selected()
    if not sel_nodes:
        LOG.warning("Select at least one node to mirror")
        return

    util = sym.MirrorUtil()
    util.isRecursive = recursive
    util.isCreationAllowed = create

    if curveShapes:
        util.add_operation(sym.MirrorCurveShapes())
    if reparent:
        util.add_operation(sym.MirrorParenting())
    if transform:
        # TODO: configure the transform util with mirror mode, etc
        util.add_operation(sym.MirrorTransforms())
    if appearance:
        blueprint = getEditorBlueprint()
        if blueprint:
            namesOp = sym.MirrorNames()
            namesOp.blueprint = blueprint
            util.add_operation(namesOp)
            colorsOp = sym.MirrorColors()
            colorsOp.blueprint = blueprint
            util.add_operation(colorsOp)
            jointDisplayOp = sym.MirrorJointDisplay()
            util.add_operation(jointDisplayOp)
    # run links last so that snapping to link targets has priority
    if links:
        util.add_operation(sym.MirrorLinks())

    util.run(sel_nodes)


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

    sel_skins = [skins.get_skin_from_mesh(m) for m in pm.selected()]
    sel_skins = [s for s in sel_skins if s]

    if not sel_skins:
        LOG.warning("No skins were found to save")
        return

    skins.save_skin_weights_to_file(filePath, *sel_skins)


def saveAllSkinWeights(filePath=None):
    """
    Save skin weights for all skin clusters in the scene.

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

    all_skins = pm.ls(type='skinCluster')

    if not all_skins:
        LOG.warning("No skins were found to save")
        return

    LOG.info(f"Saving sking weights: {all_skins}")

    skins.save_skin_weights_to_file(filePath, *all_skins)


def getNamedColor(name: str) -> Optional[LinearColor]:
    """
    Return a color by name from the config of the editor Blueprint
    """
    blueprint = getEditorBlueprint()
    if blueprint:
        config = blueprint.get_config()
        color_config = config.get('colors', {})
        hex_color = color_config.get(name)
        if hex_color:
            return LinearColor.from_hex(hex_color)


def getColorName(color: LinearColor) -> Optional[str]:
    """
    Return the name of a color as defined in the config of the editor Blueprint.
    """
    blueprint = getEditorBlueprint()
    if blueprint:
        color_config = blueprint.get_config().get('colors', {})
        # build a reverse map of names indexed by color
        colors_to_names = {h: n for n, h in color_config.items()}
        hex_color = color.as_hex()
        return colors_to_names.get(hex_color)


def setOverrideColorForSelected(color):
    """
    Set the display override color for the selected nodes
    """
    for node in pm.selected():
        nodes.setOverrideColor(node, color)


def disableColorOverrideForSelected():
    for node in pm.selected():
        nodes.disableColorOverride(node)


def openBlueprintConfigInSourceEditor():
    """
    Open the current Blueprint's config in a source editor.
    """
    blueprint = getEditorBlueprint()
    if blueprint:
        sourceeditor.open_file(blueprint.config_file_path)
