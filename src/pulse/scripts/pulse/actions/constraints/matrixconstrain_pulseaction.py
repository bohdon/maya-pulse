import pulse.nodes
from pulse.core.buildItems import BuildAction, BuildActionError


class MatrixConstrainAction(BuildAction):

    def getMinApiVersion(self):
        return 20200000

    def validate(self):
        if not self.leader:
            raise BuildActionError("leader must be set")
        if not self.follower:
            raise BuildActionError("follower must be set")

    def run(self):
        pulse.nodes.connectOffsetMatrix(
            self.leader, self.follower, True, self.preservePosition)
