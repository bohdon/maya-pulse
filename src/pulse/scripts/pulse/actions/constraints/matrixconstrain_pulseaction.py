import pulse.nodes
from pulse.buildItems import BuildAction, BuildActionError


class MatrixConstrainAction(BuildAction):

    def getMinApiVersion(self):
        return 20200000

    def validate(self):
        if not self.leader:
            raise BuildActionError("leader must be set")
        if not self.follower:
            raise BuildActionError("follower must be set")

    def run(self):
        pulse.nodes.connectOffsetMatrix(self.leader.wm, self.follower, self.method)
