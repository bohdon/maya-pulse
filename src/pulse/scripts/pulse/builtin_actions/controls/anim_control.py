import pymel.core as pm

from pulse import nodes, util_nodes
from pulse.vendor import pymetanode as meta
from pulse.core import BuildAction
from pulse.core import BuildActionAttributeType as AttrType
from pulse.anim_interface import ANIM_CTL_METACLASS, get_all_anim_ctls
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
    display_name = "Anim Control"
    color = COLOR
    category = CATEGORY
    attr_definitions = [
        dict(
            name="controlNode",
            type=AttrType.NODE,
            description="The control node to mark as an animation control",
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

    def run(self):
        # add metaclass to the control, making it
        # easy to search for by anim tools, etc
        meta.set_metadata(self.controlNode, ANIM_CTL_METACLASS, {})

        if self.zeroOutMethod == 1:
            # freeze offset matrix
            nodes.freeze_offset_matrix(self.controlNode)
        elif self.zeroOutMethod == 2:
            # create an offset transform
            nodes.create_offset_transform(self.controlNode)

        # lockup attributes
        keyable_attrs = nodes.get_expanded_attr_names(self.keyableAttrs)
        locked_attrs = nodes.get_expanded_attr_names(["t", "r", "rp", "s", "sp", "ra", "sh", "v"])
        locked_attrs = list(set(locked_attrs) - set(keyable_attrs))

        for attrName in keyable_attrs:
            attr = self.controlNode.attr(attrName)
            attr.setKeyable(True)

        for attrName in locked_attrs:
            attr = self.controlNode.attr(attrName)
            attr.setKeyable(False)
            attr.showInChannelBox(False)
            attr.setLocked(True)

        # show rotate order in channel box
        self.controlNode.rotateOrder.setLocked(True)
        self.controlNode.rotateOrder.showInChannelBox(True)

        # update rig meta data
        self.extend_rig_metadata_list("animControls", [self.controlNode])


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
