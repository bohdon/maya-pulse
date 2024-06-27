from pulse.core import BuildAction, create_rig_node
from pulse.core import BuildActionAttributeType as AttrType
from . import COLOR, CATEGORY


class CreateRigAction(BuildAction):
    """
    Create the main rig node.
    """

    id = "Pulse.CreateRig"
    display_name = "Create Rig"
    color = COLOR
    category = CATEGORY

    attr_definitions = [
        dict(
            name="rigName",
            type=AttrType.STRING,
            value="new_rig",
            description="The name of the rig node",
        )
    ]

    def should_abort_on_error(self) -> bool:
        # many actions will fail without a rig node
        return True

    def run(self):
        extra_data = {"version": self.blueprint.version}
        self.rig = create_rig_node(self.rigName, extra_data)

        self.logger.debug("Created rig node: %s", self.rig.nodeName())

        # set the rig node on the builder, so it will be provided to all future actions
        self.builder.set_rig(self.rig)
