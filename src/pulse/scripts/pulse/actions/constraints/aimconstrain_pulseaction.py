
import pymel.core as pm

import pulse.nodes
import pulse.utilnodes
from pulse.core.buildItems import BuildAction, BuildActionError


class AimConstrainAction(BuildAction):

    def validate(self):
        if not self.leader:
            raise BuildActionError("leader must be set")
        if not self.follower:
            raise BuildActionError("follower must be set")
        if not self.worldUpObject:
            raise BuildActionError("worldUpObject must be set")

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

        # create blend
        if self.createBlend:
            # create 2 more transforms to represent aiming off/on
            aimOffNode = pm.group(empty=True, p=_follower,
                                  name='%s_aimOff' % self.follower.nodeName())
            aimOnNode = pm.group(empty=True, p=_follower,
                                 name='%s_aimOn' % self.follower.nodeName())

            # move new nodes so they are siblings
            # (originally parented to follower to inherit the same transform)
            aimOffNode.setParent(_follower.getParent())
            aimOnNode.setParent(_follower.getParent())

            # create matrix blend between off and on
            wtAdd = pm.createNode('wtAddMatrix')
            aimOnNode.worldMatrix >> wtAdd.wtMatrix[0].matrixIn
            aimOffNode.worldMatrix >> wtAdd.wtMatrix[1].matrixIn
            pulse.utilnodes.connectMatrix(wtAdd.matrixSum, _follower)

            # create blend attr and connect to matrix blend
            self.follower.addAttr("aimBlend", min=0, max=1, at='double',
                                  defaultValue=1, keyable=1)
            blendAttr = self.follower.attr("aimBlend")
            blendAttr >> wtAdd.wtMatrix[0].weightIn
            pulse.utilnodes.reverse(blendAttr) >> wtAdd.wtMatrix[1].weightIn

            # use aimOn node as new follower for the aim constraint
            _follower = aimOnNode

        # create aim constrain
        upTypeStr = [
            'objectrotation',
            'object',
        ][self.worldUpType]
        ac = pm.aimConstraint(
            self.leader, _follower, mo=False,
            aimVector=self.aimVector, upVector=self.upVector,
            worldUpType=upTypeStr, worldUpObject=self.worldUpObject,
            worldUpVector=self.worldUpVector)

        # lockup the constraints
        pulse.nodes.setConstraintLocked(ac, True)
