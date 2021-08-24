import pymel.core as pm

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

        if self.preservePosition:
            follower_pm = self.follower.pm.get()
            fk_offset = follower_pm * self.fkLeader.wim.get()
            ik_offset = follower_pm * self.ikLeader.wim.get()
            fk_mtx = pulse.utilnodes.multMatrix(pm.dt.Matrix(fk_offset), self.fkLeader.wm)
            fk_mtx.node().rename(f"{self.follower.nodeName()}_ikfk_fk_offset")
            ik_mtx = pulse.utilnodes.multMatrix(pm.dt.Matrix(ik_offset), self.ikLeader.wm)
            ik_mtx.node().rename(f"{self.follower.nodeName()}_ikfk_ik_offset")
            mtx_choice = pulse.utilnodes.choice(ik_attr, fk_mtx, ik_mtx)
        else:
            mtx_choice = pulse.utilnodes.choice(ik_attr, self.fkLeader.wm, self.ikLeader.wm)

        mtx_choice.node().rename(f"{self.follower.nodeName()}_ikfk_choice")

        # don't preserve position here, because offsets have already been calculated above
        pulse.nodes.connectMatrix(mtx_choice, self.follower, pulse.nodes.ConnectMatrixMethod.SNAP)
