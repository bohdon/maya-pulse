import pulse.nodes
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType

try:
    import resetter
except ImportError:
    resetter = None

import pulse.animinterface


class SetAttributeDefaultsAction(BuildAction):

    def validate(self):
        if not resetter:
            raise BuildActionError('resetter module is not installed')

    def run(self):
        nodes = set(self.nodes)

        if self.useAnimControls:
            nodes.update(pulse.animinterface.getAllAnimControls())

        nodes = list(nodes)
        resetter.setDefaults(nodes, self.extraAttrs, nonkey=self.includeNonKeyable)
