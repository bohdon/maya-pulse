import pymel.core as pm

from pulse import names, nodes, spaces
from pulse.vendor import pymetanode as meta
from pulse.core import BuildAction, BlueprintGlobalValidateStep
from pulse.core import BuildActionAttributeType as AttrType
from pulse.ui.contextmenus import PulseNodeContextSubMenu

from . import COLOR, CATEGORY


class SpacesGlobalValidateStep(BlueprintGlobalValidateStep):
    def validate(self):
        # check for exactly 1 Apply Spaces action
        num_applies = 0
        for step, action, _ in self.all_actions:
            if action.id == ApplySpacesAction.id:
                num_applies += 1

        if num_applies == 0:
            self.logger.error("Missing required Apply Spaces action, space constraints will not work.")


class CreateSpaceAction(BuildAction):
    """
    Create a Space that can be used for dynamic constraints.
    """

    id = "Pulse.CreateSpace"
    display_name = "Create Space"
    color = COLOR
    category = CATEGORY
    sort_order = 0

    attr_definitions = [
        dict(
            name="node",
            type=AttrType.NODE,
        ),
        dict(
            name="name",
            type=AttrType.STRING,
        ),
    ]

    def run(self):
        spaces.create_space(self.node, self.name)
        self.update_rig_metadata_dict("spaces", {self.name: self.node})


class SpaceConstrainAction(BuildAction):
    """
    Creates a dynamic constraint to one or more defined spaces
    """

    id = "Pulse.SpaceConstrain"
    display_name = "Space Constrain"
    color = COLOR
    category = CATEGORY
    sort_order = 1
    global_validates = [SpacesGlobalValidateStep]

    attr_definitions = [
        dict(
            name="node",
            type=AttrType.NODE,
        ),
        dict(
            name="spaces",
            optional=False,
            type=AttrType.STRING_LIST,
        ),
        dict(
            name="useOffsetMatrix",
            type=AttrType.BOOL,
            value=True,
            description="If true, constrain the node using offsetParentMatrix, "
            "and avoid creating anextra offset transform.",
        ),
    ]

    def get_min_api_version(self):
        if self.useOffsetMatrix:
            return 20200000
        return 0

    def run(self):
        follower = None
        if not self.useOffsetMatrix:
            # create an offset transform to be constrained
            follower = nodes.create_offset_transform(self.node, "{0}_spaceConstraint")
        # set up the constraint, which will be finalized during the ApplySpaces action
        spaces.setup_space_constraint(self.node, self.spaces, follower=follower, use_offset_matrix=self.useOffsetMatrix)


class ApplySpacesAction(BuildAction):
    """
    Resolves and connects all Space Constraints in the rig
    """

    id = "Pulse.ApplySpaces"
    display_name = "Apply Spaces"
    color = COLOR
    category = CATEGORY
    sort_order = 2

    attr_definitions = [
        dict(
            name="createWorldSpace",
            type=AttrType.BOOL,
            value=True,
            description="Automatically create a 'world' space node.",
        )
    ]

    def run(self):
        if self.createWorldSpace:
            world_node = pm.group(name="world_space", empty=True, parent=self.rig)
            spaces.create_space(world_node, "world")
            self.update_rig_metadata_dict("spaces", {"world": world_node})

        # TODO: only gather not-yet-created constraints
        all_constraints = spaces.get_all_space_constraints()
        spaces.connect_space_constraints(all_constraints)


class SpaceSwitchUtils(object):
    @staticmethod
    def switch_space(ctl: pm.PyNode, space: str) -> bool:
        """
        Switch a control into a new space

        Args:
            ctl: A node with space switching metadata
            space: The name of the space to switch to

        Returns:
            True if the space was changed, false otherwise
        """
        meta_data = meta.get_metadata(ctl, spaces.SPACE_CONSTRAINT_METACLASS)
        space_data = [s for s in meta_data.get("spaces", []) if s["name"] == space]
        if not space_data:
            return False

        space_data = space_data[0]
        index = space_data["index"]

        # remember world matrix
        wm = ctl.wm.get()
        # change space
        ctl.attr("space").set(index)
        # restore world matrix
        nodes.set_world_matrix(ctl, wm)

        return True


class SpaceSwitchContextSubMenu(PulseNodeContextSubMenu):
    @classmethod
    def should_build_sub_menu(cls, menu) -> bool:
        # TODO: support switching multiple nodes if they have overlapping spaces
        return len(cls.get_selected_nodes_with_meta_class(spaces.SPACE_CONSTRAINT_METACLASS)) == 1

    def build_menu_items(self):
        ctl = self.get_selected_nodes_with_meta_class(spaces.SPACE_CONSTRAINT_METACLASS)[0]
        meta_data = meta.get_metadata(ctl, spaces.SPACE_CONSTRAINT_METACLASS)
        all_spaces = meta_data.get("spaces", [])
        if all_spaces:
            pm.menuItem(label="Spaces", enable=False)
            for space in all_spaces:
                index = space["index"]
                is_current = ctl.attr("space").get() == index

                title = names.to_title(space["name"])
                suffix = " (Default)" if index == 0 else ""
                prefix = "> " if is_current else "    "
                display_name = f"{prefix}{title}{suffix}"

                pm.menuItem(label=display_name, command=pm.Callback(SpaceSwitchUtils.switch_space, ctl, space["name"]))
