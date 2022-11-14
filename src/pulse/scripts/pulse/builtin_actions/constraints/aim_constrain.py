import pymel.core as pm

import pulse.nodes
import pulse.util_nodes
from pulse.core import BuildAction
from pulse.core import BuildActionAttributeType as AttrType

from . import COLOR, CATEGORY


class AimConstrainAction(BuildAction):
    """
    Create an aim constraint, optionally allowing for blending between aim and non-aim.
    """

    id = "Pulse.AimConstrain"
    display_name = "Aim Constrain"
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
            description="The node to aim at",
        ),
        dict(
            name="aimVector",
            type=AttrType.VECTOR3,
            value=[1, 0, 0],
            description="The forward vector to use for the aim",
        ),
        dict(
            name="upVector",
            type=AttrType.VECTOR3,
            value=[0, 1, 0],
            description="The local up vector to align with the target world up vector",
        ),
        dict(
            name="worldUpObject",
            type=AttrType.NODE,
            optional=True,
            description="The node to use for retrieving world up vector",
        ),
        dict(
            name="worldUpVector",
            type=AttrType.VECTOR3,
            value=[0, 1, 0],
            description="The vector that upVector should align with if using ObjectRotation",
        ),
        dict(
            name="worldUpType",
            type=AttrType.OPTION,
            value=0,
            options=["ObjectRotation", "Object"],
            description="The world up type. ObjectRotation - the upVector is aligned to match the orientation of the "
            "worldUpObject, Object - the upVector is aimed towards the worldUpObject",
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
            name="createBlend",
            type="bool",
            value=False,
            description="If true, create an offset and setup a blend attribute on the node to allow switching "
            "between aim and non-aim",
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

        # create blend
        if self.createBlend:
            # create 2 more transforms to represent aiming off/on
            aimOffNode = pm.group(empty=True, parent=_follower, name="%s_aimOff" % self.follower.nodeName())
            aimOnNode = pm.group(empty=True, parent=_follower, name="%s_aimOn" % self.follower.nodeName())

            # move new nodes so they are siblings
            # (originally parented to follower to inherit the same transform)
            aimOffNode.setParent(_follower.getParent())
            aimOnNode.setParent(_follower.getParent())

            # create matrix blend between off and on
            wt_add = pm.createNode("wtAddMatrix")
            aimOnNode.worldMatrix >> wt_add.wtMatrix[0].matrixIn
            aimOffNode.worldMatrix >> wt_add.wtMatrix[1].matrixIn
            pulse.nodes.connect_matrix(wt_add.matrixSum, _follower, pulse.nodes.ConnectMatrixMethod.SNAP)

            # create blend attr and connect to matrix blend
            self.follower.addAttr("aimBlend", min=0, max=1, attributeType="double", defaultValue=1, keyable=1)
            blend_attr = self.follower.attr("aimBlend")
            blend_attr >> wt_add.wtMatrix[0].weightIn
            pulse.util_nodes.reverse(blend_attr) >> wt_add.wtMatrix[1].weightIn

            # use aimOn node as new follower for the aim constraint
            _follower = aimOnNode

        # create aim constrain
        up_type_str = ["objectrotation", "object"][self.worldUpType]

        ac = pm.aimConstraint(
            self.leader,
            _follower,
            maintainOffset=False,
            aimVector=self.aimVector,
            upVector=self.upVector,
            worldUpType=up_type_str,
            worldUpObject=self.worldUpObject,
            worldUpVector=self.worldUpVector,
        )

        # lockup the constraints
        pulse.nodes.set_constraint_locked(ac, True)
