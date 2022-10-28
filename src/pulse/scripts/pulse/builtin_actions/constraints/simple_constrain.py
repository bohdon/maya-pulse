import pymel.core as pm

import pulse.nodes
from pulse.build_items import BuildAction, BuildActionError
from pulse.build_items import BuildActionAttributeType as AttrType


class SimpleConstrainAction(BuildAction):
    """
    Create a simple full constraint between nodes.
    """

    id = 'Pulse.SimpleConstrain'
    display_name = 'Simple Constrain'
    color = [.4, .6, .8]
    category = 'Constraints'

    attr_definitions = [
        dict(name='leader', type=AttrType.NODE),
        dict(name='follower', type=AttrType.NODE),
        dict(name='createFollowerOffset', type=AttrType.OPTION, value=1, options=['Always', 'Exclude Joints'],
             description="Creates and constrains a parent transform for the follower node, instead of constraining "
                         "the follower itself"),
        dict(name='worldSpaceScaling', type=AttrType.BOOL, value=False,
             description="Causes scale constraint to consider world space matrices to better handle situations where "
                         "the leader and follower have different orientations"),
    ]

    def validate(self):
        if not self.leader:
            raise BuildActionError("leader must be set")
        if not self.follower:
            raise BuildActionError("follower must be set")

    def run(self):

        should_create_offset = False
        if self.createFollowerOffset == 0:
            # Always
            should_create_offset = True
        elif self.createFollowerOffset == 1 and self.follower.nodeType() != 'joint':
            # Exclude Joints and the follower is not a joint
            should_create_offset = True

        _follower = self.follower
        if should_create_offset:
            _follower = pulse.nodes.create_offset_transform(self.follower)

        # parent constrain (translate and rotate)
        pc = pm.parentConstraint(self.leader, _follower, mo=True)
        # set interpolation mode to Shortest
        pc.interpType.set(2)

        # scale constrain
        sc = pm.scaleConstraint(self.leader, _follower, mo=True)
        if self.worldSpaceScaling:
            pulse.nodes.convert_scale_constraint_to_world_space(sc)

        # lockup the constraints
        pulse.nodes.set_constraint_locked(pc, True)
        pulse.nodes.set_constraint_locked(sc, True)
