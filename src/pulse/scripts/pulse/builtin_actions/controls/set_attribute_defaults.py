from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType

try:
    import resetter
except ImportError:
    resetter = None

import pulse.animinterface


class SetAttributeDefaultsAction(BuildAction):
    id = 'Pulse.SetAttributeDefaults'
    display_name = 'Set Attribute Defaults'
    description = 'Sets the default attribute values for use with Resetter'
    color = (.85, .65, .4)
    category = 'Controls'

    attr_definitions = [
        dict(name='useAnimControls', type=AttrType.BOOL, value=True,
             description="If true, set defaults for all animation controls, "
                         "works in addition to the explicit Nodes list."),
        dict(name='nodes', type=AttrType.NODE_LIST, optional=True,
             description="The list of nodes to set defaults on."),
        dict(name='extraAttrs', type=AttrType.STRING_LIST, value=['space'],
             description="List of extra attributes to set defaults for."),
        dict(name='includeNonKeyable', type=AttrType.BOOL, value=False,
             description="If true, set defaults for all keyable and non-keyable as well. "
                         "Does not prevent non-keyable attributes from being added in extraAttrs."),
    ]

    def validate(self):
        if not resetter:
            raise BuildActionError("'resetter' module not found")

    def run(self):
        all_nodes = set(self.nodes)

        if self.useAnimControls:
            all_nodes.update(pulse.animinterface.getAllAnimControls())

        all_nodes = list(all_nodes)
        resetter.setDefaults(all_nodes, self.extraAttrs, nonkey=self.includeNonKeyable)
