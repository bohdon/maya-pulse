import re

from maya import cmds
import pymel.core as pm

from pulse import nodes, util_nodes
from pulse.vendor import pymetanode as meta
from pulse.core import BuildAction
from pulse.core import BuildActionAttributeType as AttrType
from pulse.anim_interface import ANIM_CTL_METACLASS, get_all_anim_ctls
from pulse.control_shapes import CONTROL_SHAPE_METACLASS
from pulse.ui.contextmenus import PulseNodeContextSubMenu

from . import COLOR, CATEGORY

try:
    import resetter
except ImportError:
    resetter = None


class AnimControlAction(BuildAction):
    """
    Configure a node to be used as an animation control.
    """

    id = "Pulse.AnimControl"
    display_name = "Anim Controls"
    color = COLOR
    category = CATEGORY
    attr_definitions = [
        dict(
            name="useAllControls",
            type=AttrType.BOOL,
            value=True,
            description="Use all controls in the scene. Requires the controls to be "
            "created with the Design Toolkit or tagged as control shapes manually. Skips controls "
            "that are already setup for animation, so custom controls should precede this action.",
        ),
        dict(
            name="controlNodes",
            type=AttrType.NODE_LIST,
            optional=True,
            description="The control nodes to mark as animation controls.",
        ),
        dict(
            name="zeroOutMethod",
            type=AttrType.OPTION,
            value=1,
            options=[
                "None",
                "Offset Matrix",
                "Insert Transform",
            ],
            description="Which method to use to ensure the control transform attributes are zeroed by"
            "default in the current possition",
        ),
        dict(
            name="keyableAttrs",
            type=AttrType.STRING_LIST,
            value=["t", "r", "s"],
            canMirror=False,
            description="Defines attributes that can be animated. All others will be locked.",
        ),
    ]

    def get_min_api_version(self):
        if self.zeroOutMethod == 1:
            return 20200000
        return 0

    def validate(self):
        """
        Validate that the animation control is named, and it's scales are frozen.
        """
        # check for at least 1 control
        if self.useAllControls:
            control_nodes = meta.find_meta_nodes(CONTROL_SHAPE_METACLASS)
            if not control_nodes:
                self.logger.error("No controls were found in the scene.")
        else:
            control_nodes = self.controlNodes
            if not control_nodes:
                self.logger.error(f"Control Nodes is not set.")

        # check for unfrozen scales
        unfrozen_ctls = []
        for ctl in control_nodes:
            scale = ctl.scale.get()
            if scale != pm.dt.Vector.one:
                unfrozen_ctls.append(ctl)
        if unfrozen_ctls:
            self.logger.error(f"{len(unfrozen_ctls)} controls have unfrozen scales.")

        # check for non-unique controls
        for ctl in control_nodes:
            if not ctl.isUniquelyNamed():
                self.logger.error(f"{ctl} is not uniquely named.")

        # check for unnamed controls
        names_config = self.blueprint.get_config().get("names", {})
        pattern_fmt_str = names_config.get("anim_ctl_pattern")
        if pattern_fmt_str:
            # the pattern format contains {name}, and needs surrounding ^ and $
            pattern_str = "^" + pattern_fmt_str.format(name=".*") + "$"
            pattern_re = re.compile(pattern_str)
            for ctl in control_nodes:
                if not pattern_re.match(ctl.nodeName()):
                    self.logger.warning(f"{ctl} does not follow the naming convention: {pattern_fmt_str}")

    def run(self):
        if self.useAllControls:
            control_nodes = meta.find_meta_nodes(CONTROL_SHAPE_METACLASS)
        else:
            control_nodes = self.controlNodes

        # filter out controls that are already marked as animation controls
        control_nodes = [ctl for ctl in control_nodes if not meta.has_metaclass(ctl, ANIM_CTL_METACLASS)]

        for ctl in control_nodes:
            # add metaclass to the control, making it
            # easy to search for by anim tools, etc
            meta.set_metadata(ctl, ANIM_CTL_METACLASS, {}, undoable=False)

            if self.zeroOutMethod == 1:
                # freeze offset matrix
                nodes.freeze_offset_matrix(ctl)
            elif self.zeroOutMethod == 2:
                # create an offset transform
                nodes.create_offset_transform(ctl)

            # lockup attributes
            keyable_attrs = nodes.get_expanded_attr_names(self.keyableAttrs)
            locked_attrs = nodes.get_expanded_attr_names(["t", "r", "rp", "s", "sp", "ra", "sh", "v"])
            locked_attrs = list(set(locked_attrs) - set(keyable_attrs))

            for attrName in keyable_attrs:
                cmds.setAttr(f"{ctl}.{attrName}", edit=True, keyable=True)

            for attrName in locked_attrs:
                cmds.setAttr(f"{ctl}.{attrName}", edit=True, keyable=False, channelBox=False, lock=True)

            # show rotate order in channel box
            cmds.setAttr(f"{ctl}.rotateOrder", edit=True, lock=True, channelBox=True)

        # update rig meta data
        self.extend_rig_metadata_list("animControls", control_nodes)


class AnimControlContextSubMenu(PulseNodeContextSubMenu):
    """
    Context menu for working with animation controls.
    """

    @classmethod
    def should_build_sub_menu(cls, menu) -> bool:
        return cls.is_node_with_metaclass_selected(ANIM_CTL_METACLASS)

    def build_menu_items(self):
        pm.menuItem(
            label="Reset",
            radialPosition=self.get_safe_radial_position("N"),
            command=pm.Callback(self.resetSelected),
        )

    def resetSelected(self):
        if resetter:
            sel_ctls = self.get_selected_nodes_with_meta_class(ANIM_CTL_METACLASS)
            if sel_ctls:
                resetter.reset(sel_ctls)


class ShowAllControlsAction(BuildAction):
    """
    Adds an attribute to a node that allows overriding the visibility of all anim controls to be showing.
    Should be added after all Anim Control actions, and usually on the root control.
    """

    id = "Pulse.ShowAllControls"
    display_name = "Show All Controls"
    color = COLOR
    category = "Controls"
    attr_definitions = [
        dict(
            name="node",
            type=AttrType.NODE,
            description="The node to add the attribute to, usually the root control.",
        ),
        dict(
            name="attrName",
            type=AttrType.STRING,
            value="showAllControls",
            description="The name of the attribute",
        ),
    ]

    def run(self):
        self.node.addAttr(self.attrName, attributeType="bool")
        attr = self.node.attr(self.attrName)
        attr.setKeyable(False)
        attr.showInChannelBox(True)
        self.logger.debug(f"Added attr '{self.attrName}' to {self.node}")

        all_ctls = get_all_anim_ctls()
        for ctl in all_ctls:
            inputs = ctl.visibility.inputs(plugs=True)
            if inputs:
                # attribute has input to visibility, override it with an 'or' condition
                input_attr = inputs[0]
                vis_choice = util_nodes.choice(attr, input_attr, True)
                vis_choice.node().rename(f"{ctl}_vis_override_choice")

                # connect attribute, preserving locked state
                is_locked = ctl.visibility.isLocked()
                if is_locked:
                    ctl.visibility.setLocked(False)
                vis_choice >> ctl.visibility
                if is_locked:
                    ctl.visibility.setLocked(True)

                self.logger.debug(f"Connected '{self.node}.{attr}' visibility override to '{ctl}.visibility'")
