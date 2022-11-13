import pymel.core as pm

from pulse.build_items import BuildAction, BuildActionError
from pulse.build_items import BuildActionAttributeType as AttrType


class ObjectSetAction(BuildAction):
    """
    Create an object set.
    """

    id = "Pulse.ObjectSet"
    display_name = "Object Set"
    color = (1.0, 1.0, 1.0)
    category = "Organization"

    attr_definitions = [
        dict(
            name="name",
            type=AttrType.STRING,
            description="The name of the set.",
        ),
        dict(
            name="objects",
            type=AttrType.NODE_LIST,
            description="The objects to add to the set.",
        ),
    ]

    def validate(self):
        if not len(self.name):
            raise BuildActionError("name cannot be empty")

    def run(self):
        object_set = pm.ls(self.name)
        if len(object_set) and isinstance(object_set[0], pm.nt.ObjectSet):
            object_set = object_set[0]
        else:
            object_set = pm.sets(name=self.name, empty=True)

        object_set.addMembers(self.objects)
