from pulse.core import BuildAction, BuildActionError
from pulse.core import BuildActionAttributeType as AttrType

try:
    import resetter
except ImportError:
    resetter = None

from pulse import anim_interface


class SetAttributeDefaultsAction(BuildAction):
    """
    Set the default attribute values for use with Resetter.
    """

    id = "Pulse.SetAttributeDefaults"
    display_name = "Set Attribute Defaults"
    color = (0.85, 0.65, 0.4)
    category = "Controls"

    attr_definitions = [
        dict(
            name="useAnimControls",
            type=AttrType.BOOL,
            value=True,
            description="If true, set defaults for all animation controls, "
            "works in addition to the explicit Nodes list.",
        ),
        dict(
            name="nodes",
            type=AttrType.NODE_LIST,
            optional=True,
            description="The list of nodes to set defaults on.",
        ),
        dict(
            name="extraAttrs",
            type=AttrType.STRING_LIST,
            value=["space"],
            description="List of extra attributes to set defaults for.",
        ),
        dict(
            name="includeNonKeyable",
            type=AttrType.BOOL,
            value=False,
            description="If true, set defaults for all keyable and non-keyable as well. "
            "Does not prevent non-keyable attributes from being added in extraAttrs.",
        ),
    ]

    def validate(self):
        if not resetter:
            raise BuildActionError("'resetter' module not found")

    def run(self):
        all_nodes = set(self.nodes)

        if self.useAnimControls:
            all_nodes.update(anim_interface.get_all_anim_ctls())

        all_nodes = list(all_nodes)
        resetter.setDefaults(all_nodes, self.extraAttrs, nonkey=self.includeNonKeyable)
