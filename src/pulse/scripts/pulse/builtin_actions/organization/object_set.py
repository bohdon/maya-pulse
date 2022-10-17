import pymel.core as pm

from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType


class ObjectSetAction(BuildAction):
    id = 'Pulse.ObjectSet'
    display_name = 'Object Set'
    description = 'Creates an object set'
    color = (1.0, 1.0, 1.0)
    category = 'Organization'

    attr_definitions = [
        dict(name='name', type=AttrType.STRING, description='The name of the set.'),
        dict(name='objects', type=AttrType.NODE_LIST, description='The objects to add to the set.'),
    ]

    def validate(self):
        if not len(self.name):
            raise BuildActionError('name cannot be empty')

    def run(self):
        object_set = pm.ls(self.name)
        if len(object_set) and isinstance(object_set[0], pm.nt.ObjectSet):
            object_set = object_set[0]
        else:
            object_set = pm.sets(n=self.name, empty=True)

        object_set.addMembers(self.objects)
