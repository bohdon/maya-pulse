import pymel.core as pm

import pulse.nodes
from pulse.core import BuildAction
from pulse.core import BuildActionAttributeType as AttrType

from . import COLOR, CATEGORY


class SimpleConstrainAction(BuildAction):
    """
    Create a full constraint between nodes using the legacy parent and scale constraints.
    """

    id = "Pulse.SimpleConstrain"
    display_name = "Legacy Constrain"
    color = COLOR
    category = CATEGORY

    attr_definitions = [
        dict(
            name="leader",
            type=AttrType.NODE,
        ),
        dict(
            name="follower",
            type=AttrType.NODE,
        ),
        dict(
            name="createFollowerOffset",
            type=AttrType.OPTION,
            value=1,
            options=["Always", "Exclude Joints"],
            description="Creates and constrains a parent transform for the follower node, instead of constraining "
            "the follower itself",
        ),
        dict(
            name="worldSpaceScaling",
            type=AttrType.BOOL,
            value=False,
            description="Causes scale constraint to consider world space matrices to better handle situations where "
            "the leader and follower have different orientations",
        ),
    ]

    def run(self):
        should_create_offset = False
        if self.createFollowerOffset == 0:
            # Always
            should_create_offset = True
        elif self.createFollowerOffset == 1 and self.follower.nodeType() != "joint":
            # Exclude Joints and the follower is not a joint
            should_create_offset = True

        _follower = self.follower
        if should_create_offset:
            _follower = pulse.nodes.create_offset_transform(self.follower)

        # parent constrain (translate and rotate)
        pc = pm.parentConstraint(self.leader, _follower, maintainOffset=True)
        # set interpolation mode to Shortest
        pc.interpType.set(2)

        # scale constrain
        sc = pm.scaleConstraint(self.leader, _follower, maintainOffset=True)
        if self.worldSpaceScaling:
            pulse.nodes.convert_scale_constraint_to_world_space(sc)

        # lockup the constraints
        pulse.nodes.set_constraint_locked(pc, True)
        pulse.nodes.set_constraint_locked(sc, True)
