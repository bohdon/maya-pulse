from maya import cmds

from pulse.core.actions import BuildAction
from pulse.core.actions import BuildActionAttributeType as AttrType

from . import COLOR, CATEGORY


class LockNodeAction(BuildAction):
    """
    Lock some attributes of a node, and optionally hide it.
    """

    id = "Pulse.LockNode"
    display_name = "Lock Node"
    color = COLOR
    category = CATEGORY

    attr_definitions = [
        dict(
            name="node",
            type=AttrType.NODE,
            description="The node to lock attributes on.",
        ),
        dict(
            name="attrs",
            type=AttrType.STRING_LIST,
            value=["t", "r", "s", "v"],
            canMirror=False,
            description="The attributes to lock.",
        ),
        dict(
            name="hide",
            type=AttrType.BOOL,
            value=False,
            description="Hide the node (remains visible in debug builds).",
        ),
    ]

    def run(self):
        if self.hide and not self.builder.debug:
            cmds.setAttr(f"{self.node}.visibility", False)

        for attr in self.attrs:
            cmds.setAttr(f"{self.node}.{attr}", edit=True, lock=True, keyable=False)
