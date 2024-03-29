import pulse.nodes
from pulse.core import BuildAction
from pulse.core import BuildActionAttributeType as AttrType

from . import COLOR, CATEGORY


class MatrixConstrainAction(BuildAction):
    """
    Constrain nodes using offset parent matrix connections.
    """

    id = "Pulse.MatrixConstrain"
    display_name = "Matrix Constrain"
    color = COLOR
    category = CATEGORY
    attr_definitions = [
        dict(
            name="leader",
            type=AttrType.NODE,
        ),
        dict(
            name="follower",
            type=AttrType.NODE,
        ),
        dict(
            name="method",
            type=AttrType.OPTION,
            value=1,
            options=[
                "Connect Only",
                "Snap",
                "Keep World",
                "Create Offset",
            ],
            description="The method to use for connecting the matrix. Connect Only: only connect the offset parent"
            "matrix, keep all other attributes the same. Snap: zero out all relative transform values once"
            "connected. Keep World: restore the previous world position once connected, modifying relative"
            "transform values if necessary. Create Offset: create an offset to preserve the current world"
            "position, as well as the current relative transform values",
        ),
    ]

    def get_min_api_version(self):
        return 20200000

    def run(self):
        pulse.nodes.connect_matrix(self.leader.wm, self.follower, self.method)
