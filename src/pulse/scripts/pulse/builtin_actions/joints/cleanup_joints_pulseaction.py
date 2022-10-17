import pymel.core as pm

import pulse.joints
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType


class CleanupJointsAction(BuildAction):
    id = 'Pulse.CleanupJoints'
    displayName = 'Cleanup Joints'
    description = 'Cleans up a joint hierarchy, removing end joints or modifying segment scale compensate'
    category = 'Joints'

    attr_definitions = [
        dict(name='rootJoint', type=AttrType.NODE,
             description="A root joint of a hierarchy."),
        dict(name='removeEndJoints', type=AttrType.BOOL, value=True,
             description="Delete all end joints in the hierarchy."),
        dict(name='disableScaleCompensate', type=AttrType.BOOL, value=False,
             description="Disable segment scale compensate on all joints."),
    ]

    def validate(self):
        if not self.rootJoint:
            raise BuildActionError('rootJoint must be set')

    def run(self):
        if self.removeEndJoints:
            endJoints = pulse.joints.getEndJoints(self.rootJoint)
            pm.delete(endJoints)

        if self.disableScaleCompensate:
            allJoints = self.rootJoint.listRelatives(ad=True, typ='joint')
            for joint in allJoints:
                joint.segmentScaleCompensate.set(False)
