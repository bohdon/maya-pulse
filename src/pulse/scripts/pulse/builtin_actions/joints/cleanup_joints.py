import pymel.core as pm

from pulse import joints
from pulse.build_items import BuildAction, BuildActionError
from pulse.build_items import BuildActionAttributeType as AttrType


class CleanupJointsAction(BuildAction):
    """
    Clean up a joint hierarchy, removing end joints or modifying segment scale compensate.
    """

    id = "Pulse.CleanupJoints"
    display_name = "Cleanup Joints"
    category = "Joints"

    attr_definitions = [
        dict(
            name="rootJoint",
            type=AttrType.NODE,
            description="A root joint of a hierarchy.",
        ),
        dict(
            name="removeEndJoints",
            type=AttrType.BOOL,
            value=True,
            description="Delete all end joints in the hierarchy.",
        ),
        dict(
            name="disableScaleCompensate",
            type=AttrType.BOOL,
            value=False,
            description="Disable segment scale compensate on all joints.",
        ),
    ]

    def validate(self):
        if not self.rootJoint:
            raise BuildActionError("rootJoint must be set")

    def run(self):
        if self.removeEndJoints:
            end_joints = joints.get_end_joints(self.rootJoint)
            pm.delete(end_joints)

        if self.disableScaleCompensate:
            all_joints = self.rootJoint.listRelatives(allDescendants=True, typ="joint")
            for joint in all_joints:
                joint.segmentScaleCompensate.set(False)
