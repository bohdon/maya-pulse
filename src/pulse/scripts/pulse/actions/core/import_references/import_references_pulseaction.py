
import pymel.core as pm
import pulse
import pulse.references


class ImportReferencesAction(pulse.BuildAction):

    def run(self):
        pulse.references.importAllReferences(
            loadUnloaded=self.loadUnloaded,
            depthLimit=self.depthLimit,
            removeNamespace=self.removeNamespace
        )

