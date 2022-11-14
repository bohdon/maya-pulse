from pulse.core import BuildAction, BlueprintSettings, create_rig_node, RIG_METACLASS
from pulse.vendor import pymetanode as meta

from . import COLOR, CATEGORY


class CreateRigAction(BuildAction):
    """
    Create the main rig node.
    """

    id = "Pulse.CreateRig"
    display_name = "Create Rig"
    color = COLOR
    category = CATEGORY

    def should_abort_on_error(self) -> bool:
        # many actions will fail without a rig node
        return True

    def run(self):
        node_name_format = self.blueprint.get_setting(BlueprintSettings.RIG_NODE_NAME_FORMAT)
        rig_name = self.blueprint.get_setting(BlueprintSettings.RIG_NAME)
        rig_node_name = node_name_format.format(rigName=rig_name)
        self.rig = create_rig_node(rig_node_name)

        # add some additional meta data
        meta.update_metadata(
            self.rig,
            RIG_METACLASS,
            dict(version=self.blueprint.version),
        )
        self.logger.debug("Created rig node: %s", self.rig.nodeName())

        # set the rig node on the builder, so it will be provided to all future actions
        self.builder.rig = self.rig
