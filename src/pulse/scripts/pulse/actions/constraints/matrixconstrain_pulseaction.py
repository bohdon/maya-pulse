
import pymel.core as pm
import pymetanode as meta

import pulse
import pulse.nodes


class MatrixConstrainAction(pulse.BuildAction):

    def getMinApiVersion(self):
        return 20200000

    def validate(self):
        if not self.leader:
            raise pulse.BuildActionError("leader must be set")
        if not self.follower:
            raise pulse.BuildActionError("follower must be set")

    def run(self):
        pulse.nodes.connectOffsetMatrix(
            self.leader, self.follower, True, self.preservePosition)
