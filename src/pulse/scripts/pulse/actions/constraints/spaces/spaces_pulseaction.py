
import pymel.core as pm

import pulse
import pulse.spaces


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
        pulse.spaces.defineSpaceConstraint(self.node, self.spaces)


class ApplySpacesAction(pulse.BuildAction):

    def validate(self):
        pass

    def run(self):
        allConstraints = pulse.spaces.getAllSpaceConstraints()
        for constraint in allConstraints:
            pulse.spaces.applySpaceConstraint(constraint)
