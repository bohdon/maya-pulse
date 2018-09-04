
import pymel.core as pm
import pymetanode as meta

import pulse
import pulse.spaces
import pulse.nodes


class CreateSpaceAction(pulse.BuildAction):

    def validate(self):
        if not self.node:
            raise pulse.BuildActionError("node is not set")
        if not self.name:
            raise pulse.BuildActionError("name is empty")

    def run(self):
        pulse.spaces.createSpace(self.node, self.name)


class SpaceConstrainAction(pulse.BuildAction):

    def validate(self):
        if not self.node:
            raise pulse.BuildActionError("node is not set")
        if not self.spaces:
            raise pulse.BuildActionError("no spaces were set")

    def run(self):
        # create an offset transform to be constrained
        follower = pulse.nodes.createOffsetGroup(self.node, '{0}_spaceConstraint')
        pulse.spaces.prepareSpaceConstraint(self.node, follower, self.spaces)


class ApplySpacesAction(pulse.BuildAction):

    def validate(self):
        pass

    def run(self):
        # TODO: only gather not-yet-created constraints
        allConstraints = pulse.spaces.getAllSpaceConstraints()
        pulse.spaces.createSpaceConstraints(allConstraints)
