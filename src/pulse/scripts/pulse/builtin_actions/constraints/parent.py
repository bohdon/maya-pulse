from pulse.core import BuildAction, BuildActionError
from pulse.core import BuildActionAttributeType as AttrType


class ParentAction(BuildAction):
    """
    Parent a node to another node.
    """

    id = "Pulse.ParentAction"
    display_name = "Parent"
    color = [0.4, 0.6, 0.8]
    category = "Constraints"
    attr_definitions = [
        dict(
            name="parent",
            type=AttrType.NODE,
        ),
        dict(
            name="child",
            type=AttrType.NODE,
        ),
    ]

    def run(self):
        self.child.setParent(self.parent)
