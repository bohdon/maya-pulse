import pymel.core as pm

from pulse import nodes, utilnodes
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType


class TwistJointsAction(BuildAction):
    id = 'Pulse.TwistJoints'
    display_name = 'Twist Joints'
    description = 'Sets up twist joints to solve deformation problems in areas like the arms and legs'
    category = 'Joints'

    attr_definitions = [
        dict(name='twistJoint', type=AttrType.NODE,
             description="The joint that should twist automatically based on other joints"),
        dict(name='alignJoint', type=AttrType.NODE,
             description="The joint that the twist joint should use to determine its twist, e.g. should for "
                         "upper arm twist, or hand for lower arm twist"),
        dict(name='forwardAxis', type=AttrType.VECTOR3, value=[1, 0, 0],
             description="The forward axis of the joint that should be preserved"),
        dict(name='alignAxis', type=AttrType.VECTOR3, value=[0, 0, 1],
             description="The secondary axis used to align the twist joint with the align joint. "
                         "Recommended to use up axis for shoulders, and left axis for hands."),
        dict(name='alignToRestPose', type=AttrType.BOOL, value=False,
             description="When true, align to the the un-rotated or resting position of the align joint. "
                         "This is useful for making a twist joint that un-twists rotates from a parent align "
                         "joint, such as in the upper arm."),
        dict(name='twistControls', type=AttrType.NODE_LIST, optional=True,
             description="List of anim controls to add the twist attribute to, "
                         "which is used for blending how much twist to apply."),
    ]

    def validate(self):
        if not self.twistJoint:
            raise BuildActionError('twistJoint must be set')
        if not self.alignJoint:
            raise BuildActionError('alignJoint must be set')

    def run(self):
        twist_blend = None
        if self.twistControls:
            # add attr to first control, then add proxy to the rest
            for twist_ctl in self.twistControls:
                if twist_blend is None:
                    twist_ctl.addAttr('twistBlend', at='double', min=0, max=1, keyable=True, defaultValue=1)
                    twist_blend = twist_ctl.attr('twistBlend')
                else:
                    twist_ctl.addAttr('twistBlend', proxy=twist_blend)
        else:
            # add attr directly to joint, not usually desired because this can export with the joints as a curve
            self.twistJoint.addAttr('twistBlend', at='double', min=0, max=1, keyable=True, defaultValue=1)
            twist_blend = self.twistJoint.attr('twistBlend')

        # get parent world matrix
        parent_mtx = self._get_parent_matrix(self.twistJoint)

        if self.alignToRestPose:
            # Use the current world matrix of the align joint to calculate and store the resting position as
            # an offset applied to the joints parent node. The align joint's parentMatrix attr can't be used here,
            # since it may be driven directly by a control, and would then be equal to the animated world matrix.
            # TODO: might want to expose an option for selecting the parent node explicitly.
            align_parent = self.alignJoint.getParent()
            if align_parent:
                # get align joint matrix relative to it's parent,
                # don't trust the local matrix since inheritsTransform may not be used
                offset_mtx = self.alignJoint.wm.get() * align_parent.wim.get()
                align_tgt_mtx = utilnodes.mult_matrix(offset_mtx, align_parent.wm)
                pass
            else:
                # no parent node, just store the current 'resting' matrix in a multMatrix
                align_tgt_mtx = utilnodes.mult_matrix(self.alignJoint.wm.get())
        else:
            # use to align joint world matrix directly
            align_tgt_mtx = self.alignJoint.wm

        # create aligned version of the parent matrix
        aligned_pm = utilnodes.align_matrix_to_direction(parent_mtx, self.forwardAxis, self.alignAxis,
                                                         self.alignAxis, align_tgt_mtx)

        # blend aligned matrix with default parent matrix
        blend_mtx = utilnodes.blend_matrix(parent_mtx, aligned_pm, twist_blend)

        nodes.connectMatrix(blend_mtx, self.twistJoint, nodes.ConnectMatrixMethod.CREATE_OFFSET)

    def _get_parent_matrix(self, node):
        """
        Return the parent world matrix to use for a node, checking first for inputs to offsetParentMatrix,
        then for a parent node if available. Does not support nodes that have a connection to offsetParentMatrix
        while also having inheritsTransform set to True.
        """
        # look for and use input to offsetParentMatrix if available
        offset_mtx_inputs = node.offsetParentMatrix.inputs(plugs=True)
        if offset_mtx_inputs:
            if node.inheritsTransform.get():
                raise BuildActionError(f"{node} cannot have an offsetParentMatrix connection "
                                       "while also having inheritsTransform set to True")
            return offset_mtx_inputs[0]

        # get matrix from parent node
        parent_node = node.getParent()
        if parent_node:
            return parent_node.wm

        # no parent, use identity matrix
        return pm.dt.Matrix()
