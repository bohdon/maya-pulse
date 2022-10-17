import pulse.references
from pulse.buildItems import BuildAction
from pulse.buildItems import BuildActionAttributeType as AttributeType


class ImportReferencesAction(BuildAction):
    id = 'Pulse.ImportReferences'
    display_name = 'Import References'
    description = 'Import all file references into the scene.'
    category = 'Core'
    attr_definitions = [
        dict(name='loadUnloaded', type=AttributeType.BOOL, value=True),
        dict(name='depthLimit', type=AttributeType.INT, value=10, min=1),
        dict(name='removeNamespace', type=AttributeType.BOOL, value=True),
    ]

    def run(self):
        pulse.references.importAllReferences(
            loadUnloaded=self.loadUnloaded,
            depthLimit=self.depthLimit,
            removeNamespace=self.removeNamespace
        )
