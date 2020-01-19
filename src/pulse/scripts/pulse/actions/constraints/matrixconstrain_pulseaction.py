
import pymel.core as pm
import pymetanode as meta

import pulse
import pulse.nodes


class MatrixConstrainAction(pulse.BuildAction):

    def validate(self):
        if not self.leader:
            raise pulse.BuildActionError("leader must be set")
        if not self.follower:
            raise pulse.BuildActionError("follower must be set")

    def run(self):
        if self.preservePosition:
            # preserve world space matrix of the follower,
            # since it may jump once we connect a non-zero parent matrix
            wm = pulse.nodes.getWorldMatrix(self.follower)

        self.leader.worldMatrix >> self.follower.offsetParentMatrix

        if self.preservePosition:
            pulse.nodes.setWorldMatrix(self.follower, wm)
