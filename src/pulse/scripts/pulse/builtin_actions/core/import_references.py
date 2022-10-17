from pulse import references
from pulse.buildItems import BuildAction
from pulse.buildItems import BuildActionAttributeType as AttrType


class ImportReferencesAction(BuildAction):
    id = 'Pulse.ImportReferences'
    display_name = 'Import References'
    description = 'Import all file references into the scene.'
    category = 'Core'
    attr_definitions = [
        dict(name='loadUnloaded', type=AttrType.BOOL, value=True),
        dict(name='depthLimit', type=AttrType.INT, value=10, min=1),
        dict(name='removeNamespace', type=AttrType.BOOL, value=True),
    ]

    def run(self):
        references.importAllReferences(
            loadUnloaded=self.loadUnloaded,
            depthLimit=self.depthLimit,
            removeNamespace=self.removeNamespace
        )
