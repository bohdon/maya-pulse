from pulse.core import BuildAction
from pulse.core import BuildActionAttributeType as AttrType

from . import COLOR, CATEGORY


class ParentAction(BuildAction):
    """
    Parent a node to another node.
    """

    id = "Pulse.ParentAction"
    display_name = "Parent"
    color = COLOR
    category = CATEGORY
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
