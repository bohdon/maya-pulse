import pulse.references
from pulse.core.buildItems import BuildAction


class ImportReferencesAction(BuildAction):

    def run(self):
        pulse.references.importAllReferences(
            loadUnloaded=self.loadUnloaded,
            depthLimit=self.depthLimit,
            removeNamespace=self.removeNamespace
        )
