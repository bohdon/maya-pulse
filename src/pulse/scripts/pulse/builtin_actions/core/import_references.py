from pulse import references
from pulse.build_items import BuildAction
from pulse.build_items import BuildActionAttributeType as AttrType


class ImportReferencesAction(BuildAction):
    """
    Import all file references into the scene.
    """

    id = "Pulse.ImportReferences"
    display_name = "Import References"
    category = "Core"
    attr_definitions = [
        dict(
            name="loadUnloaded",
            type=AttrType.BOOL,
            value=True,
        ),
        dict(
            name="depthLimit",
            type=AttrType.INT,
            value=10,
            min=1,
        ),
        dict(
            name="removeNamespace",
            type=AttrType.BOOL,
            value=True,
        ),
    ]

    def run(self):
        references.import_all_references(
            load_unloaded=self.loadUnloaded,
            depth_limit=self.depthLimit,
            remove_namespace=self.removeNamespace,
            prompt=False,
        )
