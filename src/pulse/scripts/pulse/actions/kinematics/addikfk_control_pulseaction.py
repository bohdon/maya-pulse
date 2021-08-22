import pulse.nodes
import pulse.utilnodes
from pulse.buildItems import BuildAction, BuildActionError


class AddIKFKControlAction(BuildAction):

    def validate(self):
        if not self.ikfkControl:
            raise BuildActionError('ikfkControl must be set')
        if not self.follower:
            raise BuildActionError('follower must be set')
        if not self.ikLeader:
            raise BuildActionError('ikLeader must be set')
        if not self.fkLeader:
            raise BuildActionError('fkLeader must be set')

    def run(self):
        ik_attr = self.ikfkControl.attr('ik')
        if not ik_attr:
            raise BuildActionError(f"ikfkControl has no IK attribute: {self.ikfkControl}")

        mtx_choice = pulse.utilnodes.choice(ik_attr, self.fkLeader.wm, self.ikLeader.wm)

        pulse.nodes.connectOffsetMatrix(mtx_choice, self.follower, preservePosition=self.preservePosition)
