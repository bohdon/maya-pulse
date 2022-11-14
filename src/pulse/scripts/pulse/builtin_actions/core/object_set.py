import pymel.core as pm

from pulse.core import BuildAction
from pulse.core import BuildActionAttributeType as AttrType

from . import COLOR, CATEGORY


class ObjectSetAction(BuildAction):
    """
    Create an object set.
    """

    id = "Pulse.ObjectSet"
    display_name = "Object Set"
    color = COLOR
    category = CATEGORY

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

    def run(self):
        object_set = pm.ls(self.name)
        if len(object_set) and isinstance(object_set[0], pm.nt.ObjectSet):
            object_set = object_set[0]
        else:
            object_set = pm.sets(name=self.name, empty=True)

        object_set.addMembers(self.objects)
