import pymel.core as pm

import pulse.nodes
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType


class SimpleConstrainAction(BuildAction):
    id = 'Pulse.SimpleConstrain'
    display_name = 'Simple Constrain'
    description = 'Create a simple full constraint between nodes'
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

        shouldCreateOffset = False
        if self.createFollowerOffset == 0:
            # Always
            shouldCreateOffset = True
        elif self.createFollowerOffset == 1 and self.follower.nodeType() != 'joint':
            # Exclude Joints and the follower is not a joint
            shouldCreateOffset = True

        _follower = self.follower
        if shouldCreateOffset:
            _follower = pulse.nodes.createOffsetTransform(self.follower)

        # parent constrain (translate and rotate)
        pc = pm.parentConstraint(self.leader, _follower, mo=True)
        # set interpolation mode to Shortest
        pc.interpType.set(2)

        # scale constrain
        sc = pm.scaleConstraint(self.leader, _follower, mo=True)
        if self.worldSpaceScaling:
            pulse.nodes.convertScaleConstraintToWorldSpace(sc)

        # lockup the constraints
        pulse.nodes.setConstraintLocked(pc, True)
        pulse.nodes.setConstraintLocked(sc, True)
