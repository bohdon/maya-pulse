from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType


class ParentAction(BuildAction):
    id = 'Pulse.ParentAction'
    display_name = 'Parent'
    description = 'Parent a node to another node.'
    color = [.4, .6, .8]
    category = 'Constraints'
    attr_definitions = [
        dict(name='parent', type=AttrType.NODE),
        dict(name='child', type=AttrType.NODE),
    ]

    def validate(self):
        if not self.parent:
            raise BuildActionError("parent must be set")
        if not self.child:
            raise BuildActionError("child must be set")

    def run(self):
        self.child.setParent(self.parent)
