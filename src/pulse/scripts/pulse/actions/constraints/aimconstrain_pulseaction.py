
import pymel.core as pm
import pymetanode as meta

import pulse
import pulse.nodes


class AimConstrainAction(pulse.BuildAction):

    def validate(self):
        if not self.leader:
            raise pulse.BuildActionError("leader must be set")
        if not self.follower:
            raise pulse.BuildActionError("follower must be set")
        if not self.worldUpObject:
            raise pulse.BuildActionError("worldUpObject must be set")

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

        # create aim constrain
        upTypeStr = [
            'objectrotation',
            'object',
        ][self.worldUpType]
        ac = pm.aimConstraint(
            self.leader, _follower, mo=True,
            aimVector=self.aimVector, upVector=self.upVector,
            worldUpType=upTypeStr, worldUpObject=self.worldUpObject,
            worldUpVector=self.worldUpVector)

        # lockup the constraints
        pulse.nodes.setConstraintLocked(ac, True)

        # create blend
        if self.createBlend:
            pass
