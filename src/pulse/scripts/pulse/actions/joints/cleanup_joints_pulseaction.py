
import pymel.core as pm

import pulse
import pulse.nodes
import pulse.joints


class CleanupJointsAction(pulse.BuildAction):
    def validate(self):
        if not self.rootJoint:
            raise pulse.BuildActionError('rootJoint must be set')

    def run(self):
        if self.removeEndJoints:
            endJoints = pulse.joints.getEndJoints(self.rootJoint)
            pm.delete(endJoints)

        if self.disableScaleCompensate:
            allJoints = self.rootJoint.listRelatives(ad=True, typ='joint')
            for joint in allJoints:
                joint.segmentScaleCompensate.set(False)
