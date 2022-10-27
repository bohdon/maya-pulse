import pulse.nodes
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType


class MatrixConstrainAction(BuildAction):
    id = 'Pulse.MatrixConstrain'
    display_name = 'Matrix Constrain'
    description = 'Constrain nodes using offsetParentMatrix connections'
    category = 'Constraints'
    color = (.4, .6, .8)
    attr_definitions = [
        dict(name='leader', type=AttrType.NODE),
        dict(name='follower', type=AttrType.NODE),
        dict(name='method', type=AttrType.OPTION, value=1, options=[
            'Connect Only',
            'Snap',
            'Keep World',
            'Create Offset',
        ], description="The method to use for connecting the matrix. Connect Only: only connect the offset parent"
                       "matrix, keep all other attributes the same. Snap: zero out all relative transform values once"
                       "connected. Keep World: restore the previous world position once connected, modifying relative"
                       "transform values if necessary. Create Offset: create an offset to preserve the current world"
                       "position, as well as the current relative transform values"),
    ]

    def get_min_api_version(self):
        return 20200000

    def validate(self):
        if not self.leader:
            raise BuildActionError("leader must be set")
        if not self.follower:
            raise BuildActionError("follower must be set")

    def run(self):
        pulse.nodes.connect_matrix(self.leader.wm, self.follower, self.method)
