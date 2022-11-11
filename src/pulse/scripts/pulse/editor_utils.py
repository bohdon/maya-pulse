"""
A function library of miscellaneous utils usually involving editor selection or interactive work.

Many UI commands are located here, as they can be more specific
than the core api but still not dependent on a UI.
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
from . import source_editor
from .colors import LinearColor
from .vendor.mayacoretools import preservedSelection

LOG = logging.getLogger(__name__)


def save_scene_if_dirty(prompt=True):
    """
    Prompt the user to save if the scene is modified, or has never been saved.

    Returns True if the save was successful, or the scene has not been modified.

    Args:
        prompt (bool): If True, prompt the user, or attempt to automatically save where possible
    """
    modified = pm.cmds.file(q=True, modified=True)
    never_saved = not pm.sceneName()

    if never_saved:
        # first time saving
        if not prompt:
            pm.runtime.SaveSceneAs()
            return bool(pm.sceneName())
        else:
            # either save as or cancel
            kwargs = dict(
                title="Warning: Scene Not Saved",
                message="Save changes to untitled scene?",
                db="Save",
                cb="Cancel",
                ds="Cancel",
                button=("Save", "Cancel"),
            )
            result = pm.confirmDialog(**kwargs)
            if result == "Save":
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
                title="Save Scene",
                message=f"Save changes to\n{pm.sceneName()}",
                db="Save",
                cb="Cancel",
                ds="Cancel",
                button=("Save", "Cancel"),
            )
            result = pm.confirmDialog(**kwargs)
            if result == "Save":
                return pm.saveFile(force=True)
            else:
                return False

    else:
        return True


def get_editor_blueprint():
    """
    Return the shared Blueprint instance from the default UI model
    """
    from .ui.core import BlueprintUIModel

    return BlueprintUIModel.get_default_model().blueprint


def get_selected_transforms(include_children=False):
    """
    Return the currently selected transforms (or joints).

    Args:
        include_children (bool): If true, also include all descendants of the selected nodes.
    """
    sel = pm.selected(type=["transform", "joint"])
    if include_children:
        result = []
        for s in sel:
            if s not in result:
                result.append(s)
            for child in s.listRelatives(ad=True, type=["transform", "joint"]):
                if child not in result:
                    result.append(child)
        return result
    else:
        return sel


def center_selected_joints():
    """
    Center the selected joint
    """
    for s in pm.selected():
        joints.center_joint(s)


def disable_segment_scale_compensate_for_selected():
    """
    Disable segment scale compensation on the selected joints
    """
    for jnt in pm.selected():
        if jnt.nodeType() == "joint":
            jnt.ssc.set(False)


def insert_joint_for_selected(count=1):
    """
    Insert joints above the selected joint
    """
    result = []
    for s in pm.selected():
        result.extend(joints.insert_joints(s, count))
    pm.select(result)


def create_offset_for_selected():
    """
    Create an offset group for the selected nodes
    """
    pm.select([nodes.create_offset_transform(s) for s in pm.selected(type="transform")])


def freeze_scales_for_selected_hierarchies(skip_joints=True):
    """
    Freeze scales on the selected transforms and all their descendants.
    See `freeze_scales_for_hierarchy` for more details.

    Args:
        skip_joints (bool): If true, don't attempt to freeze joint hierarchies. Does not prevent
            freezing joints if they are a child of one of the selected transforms.
    """
    with preservedSelection() as sel:
        top_nodes = nodes.get_parent_nodes(sel[:])
        for topNode in top_nodes:
            if not skip_joints or topNode.nodeType() != "joint":
                nodes.freeze_scales_for_hierarchy(topNode)


def freeze_pivots_for_selected_hierarchies():
    with preservedSelection() as sel:
        for s in sel:
            nodes.freeze_pivots_for_hierarchy(s)


def freeze_offset_matrices_for_selected_hierarchies():
    with preservedSelection() as sel:
        for s in sel:
            nodes.freeze_offset_matrix_for_hierarchy(s)


def unfreeze_offset_matrices_for_selected_hierarchies():
    with preservedSelection() as sel:
        for s in sel:
            nodes.unfreeze_offset_matrix_for_hierarchy(s)


def freeze_joints_for_selected_hierarchies():
    """
    Freeze rotates and scales on the selected joint hierarchies.
    """
    with preservedSelection() as sel:
        top_nodes = nodes.get_parent_nodes(sel[:])
        for topNode in top_nodes:
            if topNode.nodeType() == "joint":
                joints.freeze_joints(topNode)


def parent_selected():
    """
    Parent the selected nodes. Select a leader then followers.

    [A, B, C] -> A|B, A|C
    """
    sel = pm.selected()
    if len(sel) < 2:
        pm.warning("More that one node must be selected")
        return
    nodes.set_parent(sel[1:], sel[0])
    pm.select(sel)


def parent_selected_in_order():
    """
    Parent the selected nodes to each other in order.
    Select from top of hierarchy downward, eg. [A, B, C] -> A|B|C
    """
    with preservedSelection() as sel:
        nodes.parent_in_order(sel[:])


def rotate_selected_components_around_axis(axis, degrees=90):
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


def orient_to_world_for_selected(
    include_children=False, preserve_children=True, preserve_shapes=True, sync_joint_axes=True
):
    """
    Orient the selected joints or transforms to match the world aligned axes.
    """
    # TODO: implement preserve_shapes
    sel = get_selected_transforms(include_children)
    for node in sel:
        if node.nodeType() == "joint":
            joints.orient_joint_to_world(node)
            if sync_joint_axes:
                joints.match_joint_rotation_to_orient(node, preserve_children)
        else:
            pm.rotate(node, (0, 0, 0), a=True, ws=True, pcp=preserve_children)


def orient_to_joint_for_selected(
    axis_order, up_axis_str, include_children=False, preserve_children=True, preserve_shapes=True, sync_joint_axes=True
):
    sel = get_selected_transforms(include_children)
    for node in sel:
        if node.nodeType() == "joint":
            joints.orient_joint(node, axis_order, up_axis_str)


def orient_to_parent_for_selected(include_children=False, preserve_children=True):
    sel = get_selected_transforms(include_children)
    for node in sel:
        if node.nodeType() == "joint":
            joints.orient_joint_to_parent(node, preserve_children)


def orient_ik_joints_for_selected(aim_axis="x", pole_axis="y", preserve_children=True):
    sel = pm.selected(type="joint")
    for node in sel:
        joints.orient_ik_joints(node, aim_axis=aim_axis, pole_axis=pole_axis, preserve_children=preserve_children)


def rotate_selected_orients_around_axis(
    axis, degrees=90, preserve_children=True, preserve_shapes=True, sync_joint_axes=True
):
    """
    Rotate the selected nodes around the given axis
    If the node is a joint, its jointOrient will be rotated

    Args:
        axis: The axis to rotate around.
        degrees: The degrees of rotation to apply.
        preserve_children: If true, prevent children from moving.
        preserve_shapes: If true, prevent child shapes from moving.
        sync_joint_axes (bool): If True, joints will also have their
            translate and scale axes updated to match the new orientation.
    """
    # if currently on move tool, make sure its object space
    if pm.currentCtx() == pm.melGlobals["$gMove"]:
        pm.manipMoveContext("Move", e=True, mode=0)

    rotation = pm.dt.Vector()
    rotation[axis] = degrees

    sel_nodes = pm.selected()
    for node in sel_nodes:
        rotate_orient_or_transform(node, rotation, preserve_children, preserve_shapes, sync_joint_axes)


def rotate_orient_or_transform(
    node: pm.nt.Transform, rotation: pm.dt.Vector, preserve_children=True, preserve_shapes=True, sync_joint_axes=True
):
    """
    Rotate a node in local space, or if it's a joint, by modifying the joint orient.
    Additionally, can preserve child transform positions and/or shapes (such as control cvs).

    Args:
        node: The node to rotate.
        rotation: The delta rotation to apply.
        preserve_children: If true, prevent children from moving.
        preserve_shapes: If true, prevent child shapes from moving.
        sync_joint_axes (bool): If True, joints will also have their
            translate and scale axes updated to match the new orientation.
    """
    if node.nodeType() == "joint":
        joints.rotate_joint_orient(node, rotation)
        if sync_joint_axes:
            joints.match_joint_rotation_to_orient(node, preserve_children)
    else:
        pm.rotate(node, rotation, os=True, r=True, pcp=preserve_children)

        # normalize eulers to 0..360, assumed as part of orienting
        nodes.normalize_euler_rotations(node)

        if preserve_shapes:
            node_shapes = node.getShapes()
            for shape in node_shapes:
                shapes.rotate_components(shape, -rotation)


def orient_joint_to_rotation_for_selected(include_children=False, preserve_children=True):
    sel_nodes = get_selected_transforms(include_children)
    for node in sel_nodes:
        if node.nodeType() == "joint":
            joint = node.node()
            joints.orient_joint_to_rotation(joint, preserve_children)


def interactive_orient_for_selected():
    sel = pm.selected(type="joint")
    rotate_axes = [s.rotateAxis for s in sel]
    pm.select(rotate_axes)


def fixup_joint_orient_for_selected(aim_axis="x", keep_axis="y", preserve_children=True):
    sel = pm.selected(type="joint")
    for node in sel:
        joints.fixup_joint_orient(node, aim_axis=aim_axis, keep_axis=keep_axis, preserve_children=preserve_children)


def match_joint_rotation_to_orient_for_selected(preserve_children=True):
    # handle current selection containing both joints, and possibly pivots of joints
    sel = pm.selected()
    for s in sel:
        if s.nodeType() == "joint":
            joint = s.node()
            joints.match_joint_rotation_to_orient(joint, preserve_children)


def mark_end_joints_for_selected():
    """
    Find all end joints, and rename them to END_jnt, and set their override colors
    """
    sel = pm.selected()
    for s in sel:
        end_joints = joints.get_end_joints(s)
        for end_joint in end_joints:
            end_joint.rename("END_jnt")
            end_joint.overrideEnabled.set(True)
            end_joint.overrideRGBColors.set(True)
            end_joint.overrideColorRGB.set((0.35, 0, 0))


def get_detailed_channel_box_attrs(node):
    """
    Return the list of attributes that are included
    when the 'detailed channel box' is enabled for a node.
    """
    attrs = [
        # rotate order
        "ro",
        # rotate axis
        "rax",
        "ray",
        "raz",
        # rotate pivot
        "rpx",
        "rpy",
        "rpz",
        # scale pivot
        "spx",
        "spy",
        "spz",
        # rotate pivot translate
        "rptx",
        "rpty",
        "rptz",
        # scale pivot translate
        "sptx",
        "spty",
        "sptz",
    ]

    if node.nodeType() == "joint":
        attrs += [
            # joint orient
            "jox",
            "joy",
            "joz",
        ]

    return attrs


def is_detailed_channel_box_enabled(node) -> bool:
    def is_visible_in_cb(_node, attr):
        return cmds.getAttr(_node + "." + attr, cb=True)

    attrs = get_detailed_channel_box_attrs(node)
    if any([is_visible_in_cb(node, a) for a in attrs]):
        return True


def set_detailed_channel_box_enabled(node, enabled=True):
    """
    Set whether a node should display detailed channel box
    attributes related to transforms and joint orients.
    """
    attrs = get_detailed_channel_box_attrs(node)
    for attr in attrs:
        pm.cmds.setAttr(node + "." + attr, cb=enabled)


def toggle_detailed_channel_box_for_selected():
    """
    Toggle the display of detailed channel box attributes
    for all selected nodes.
    """
    sel = pm.selected()

    is_enabled = False
    for s in sel:
        if is_detailed_channel_box_enabled(s):
            is_enabled = True
            break

    for s in sel:
        set_detailed_channel_box_enabled(s, not is_enabled)


def toggle_local_rotation_axes_for_selected(include_children=False):
    sel = get_selected_transforms(include_children)
    is_enabled = False
    for s in sel:
        if s.dla.get():
            is_enabled = True
            break

    for s in sel:
        s.dla.set(not is_enabled)


def link_selected(link_type=links.LinkType.DEFAULT, keep_offset=False):
    sel = pm.selected()
    if len(sel) < 2:
        LOG.warning("Select at least one leader, then a follower last")
        return

    positioner = links.get_positioner(link_type)
    positioner.keepOffset = keep_offset
    follower = sel[-1]
    leaders = sel[:-1]
    positioner.create_link(follower, leaders)


def link_selected_weighted(keep_offset=False):
    sel = pm.selected()
    if len(sel) < 2:
        LOG.warning("Select at least one leader, then a follower last")
        return

    positioner = links.get_positioner(links.LinkType.WEIGHTED)
    positioner.keepOffset = keep_offset
    follower = sel[-1]
    leaders = sel[:-1]
    positioner.weights = [1] * len(leaders)
    positioner.create_link(follower, leaders)


def unlink_selected():
    for s in pm.selected():
        links.unlink(s)


def recreate_links_for_selected(keep_offset=False):
    for s in pm.selected():
        links.recreate_link(s, keep_offset=keep_offset)


def upgrade_all_links():
    """
    Update all links in the scene, fixing up old data as necessary.
    """
    for n in pm.ls():
        link_data = links.get_link_meta_data(n)
        if link_data:
            changed = False

            # support legacy data of just a target node, not a dict
            if isinstance(link_data, pm.PyNode):
                link_data = {"targetNodes": [link_data]}
                changed = True

            # ensure link type key exists
            if "type" not in link_data:
                link_data["type"] = links.LinkType.DEFAULT
                changed = True

            # upgrade targetNode (single target) to targetNodes (list of targets)
            if "targetNode" in link_data:
                target_node = link_data["targetNode"]
                del link_data["targetNode"]
                link_data["targetNodes"] = [target_node]
                changed = True

            if changed:
                LOG.info("Updated link data for %s", n)
                links.set_link_meta_data(n, link_data)


def position_link_for_selected():
    sel = pm.selected()
    if not sel:
        sel = links.get_all_linked_nodes()
        # TODO: sort by parenting hierarchy
    else:
        old_len = len(sel)
        # filter for only linked nodes
        sel = [s for s in sel if links.is_linked(s)]
        if old_len > 0 and len(sel) == 0:
            # something was selected, but no linked nodes
            LOG.warning("No linked nodes were selected")

    show_progress = len(sel) > 20
    if show_progress:
        pm.progressWindow(t="Positioning Links", min=0, max=len(sel))
    for node in sel:
        links.apply_link_position(node)
        if show_progress:
            pm.progressWindow(e=True, step=1)
    if show_progress:
        pm.progressWindow(endProgress=True)


def pair_selected():
    sel = pm.selected()
    if len(sel) == 2:
        sym.pair_mirror_nodes(sel[0], sel[1])


def unpair_selected():
    for s in pm.selected():
        sym.unpair_mirror_node(s)


def mirror_selected(
    recursive=True, create=True, curve_shapes=True, links=True, reparent=True, transform=True, appearance=True
):
    """
    Perform a mirroring operation on the selected nodes.

    Args:
        recursive (bool): Mirror the selected nodes and all children
        create (bool): Allow creation of new nodes if a pair is not found
        curve_shapes (bool): Mirror control shape curves
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

    if curve_shapes:
        util.add_operation(sym.MirrorCurveShapes())
    if reparent:
        util.add_operation(sym.MirrorParenting())
    if transform:
        # TODO: configure the transform util with mirror mode, etc
        util.add_operation(sym.MirrorTransforms())
    if appearance:
        blueprint = get_editor_blueprint()
        if blueprint:
            names_op = sym.MirrorNames()
            names_op.blueprint = blueprint
            util.add_operation(names_op)
            colors_op = sym.MirrorColors()
            colors_op.blueprint = blueprint
            util.add_operation(colors_op)
            joint_display_op = sym.MirrorJointDisplay()
            util.add_operation(joint_display_op)
    # run links last so that snapping to link targets has priority
    if links:
        util.add_operation(sym.MirrorLinks())

    util.run(sel_nodes)


def save_skin_weights_for_selected(file_path=None):
    """
    Save skin weights for the selected meshes to a file.

    Args:
        file_path (str): A full path to a .weights file to write. If None,
            will use the scene name.
    """
    if file_path is None:
        scene_name = pm.sceneName()
        if not scene_name:
            LOG.warning("Scene is not saved")
            return
        file_path = os.path.splitext(scene_name)[0] + ".weights"

    sel_skins = [skins.get_skin_from_mesh(m) for m in pm.selected()]
    sel_skins = [s for s in sel_skins if s]

    if not sel_skins:
        LOG.warning("No skins were found to save")
        return

    skins.save_skin_weights_to_file(file_path, *sel_skins)


def save_all_skin_weights(file_path=None):
    """
    Save skin weights for all skin clusters in the scene.

    Args:
        file_path (str): A full path to a .weights file to write. If None,
            will use the scene name.
    """
    if file_path is None:
        scene_name = pm.sceneName()
        if not scene_name:
            LOG.warning("Scene is not saved")
            return
        file_path = f"{os.path.splitext(scene_name)[0]}.weights"

    all_skins = pm.ls(type="skinCluster")

    if not all_skins:
        LOG.warning("No skins were found to save")
        return

    LOG.info("Saving skin weights: %s", all_skins)

    skins.save_skin_weights_to_file(file_path, *all_skins)


def get_named_color(name: str) -> Optional[LinearColor]:
    """
    Return a color by name from the config of the editor Blueprint
    """
    blueprint = get_editor_blueprint()
    if blueprint:
        config = blueprint.get_config()
        color_config = config.get("colors", {})
        hex_color = color_config.get(name)
        if hex_color:
            return LinearColor.from_hex(hex_color)


def get_color_name(color: LinearColor) -> Optional[str]:
    """
    Return the name of a color as defined in the config of the editor Blueprint.
    """
    blueprint = get_editor_blueprint()
    if blueprint:
        color_config = blueprint.get_config().get("colors", {})
        # build a reverse map of names indexed by color
        colors_to_names = {h: n for n, h in color_config.items()}
        hex_color = color.as_hex()
        return colors_to_names.get(hex_color)


def set_override_color_for_selected(color):
    """
    Set the display override color for the selected nodes
    """
    for node in pm.selected():
        nodes.set_override_color(node, color)


def disable_color_override_for_selected():
    for node in pm.selected():
        nodes.disable_color_override(node)


def open_blueprint_config_in_source_editor():
    """
    Open the current Blueprint's config in a source editor.
    """
    blueprint = get_editor_blueprint()
    if blueprint:
        source_editor.open_file(blueprint.config_file_path)
