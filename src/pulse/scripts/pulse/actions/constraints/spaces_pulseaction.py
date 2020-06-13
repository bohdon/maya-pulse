
import maya.cmds as cmds

import pulse
import pulse.spaces
import pulse.nodes


class CreateSpaceAction(pulse.BuildAction):

    def validate(self):
        if not self.node:
            raise pulse.BuildActionError("node must be set")
        if not self.name:
            raise pulse.BuildActionError("name cannot be empty")

    def run(self):
        pulse.spaces.createSpace(self.node, self.name)
        self.updateRigMetaDataDict('spaces', {self.name: self.node})


class SpaceConstrainAction(pulse.BuildAction):

    def getMinApiVersion(self):
        if self.useOffsetMatrix:
            return 20200000
        return 0

    def validate(self):
        if not self.node:
            raise pulse.BuildActionError("node must be set")
        if not self.spaces:
            raise pulse.BuildActionError("spaces must have at least one value")

    def run(self):
        follower = None
        if not self.useOffsetMatrix:
            # create an offset transform to be constrained
            follower = pulse.nodes.createOffsetTransform(
                self.node, '{0}_spaceConstraint')
        # setup the constraint, which will be finalized during the ApplySpaces action
        pulse.spaces.setupSpaceConstraint(
            self.node, self.spaces, follower=follower, useOffsetMatrix=self.useOffsetMatrix)


class ApplySpacesAction(pulse.BuildAction):

    def validate(self):
        pass

    def run(self):
        # TODO: only gather not-yet-created constraints
        allConstraints = pulse.spaces.getAllSpaceConstraints()
        pulse.spaces.connectSpaceConstraints(allConstraints)
