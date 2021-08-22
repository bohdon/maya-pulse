import pymel.core as pm

import pulse.nodes
import pulse.utilnodes
from pulse.buildItems import BuildAction, BuildActionError


class TwistJointsAction(BuildAction):
    def validate(self):
        if not self.twistJoint:
            raise BuildActionError('twistJoint must be set')
        if not self.alignJoint:
            raise BuildActionError('alignJoint must be set')

    def run(self):
        # add keyable twist attribute to control the blend
        self.twistJoint.addAttr('twistBlend', at='double', min=0, max=1, keyable=True, defaultValue=1)
        twist_blend = self.twistJoint.attr('twistBlend')

        # add proxy attribute to twist controls
        for twist_ctl in self.twistControls:
            twist_ctl.addAttr('twistBlend', proxy=twist_blend)

        # get parent world matrix
        parent_mtx = self.getParentMatrix(self.twistJoint)

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
                align_tgt_mtx = pulse.utilnodes.multMatrix(offset_mtx, align_parent.wm)
                pass
            else:
                # no parent node, just store the current 'resting' matrix in a multMatrix
                align_tgt_mtx = pulse.utilnodes.multMatrix(self.alignJoint.wm.get())
        else:
            # use the align joint world matrix directly
            align_tgt_mtx = self.alignJoint.wm

        # create aligned version of the parent matrix
        aligned_pm = pulse.utilnodes.alignMatrixToDirection(parent_mtx, self.forwardAxis, self.alignAxis,
                                                            self.alignAxis, align_tgt_mtx)

        # blend aligned matrix with default parent matrix
        blend_mtx = pulse.utilnodes.blendMatrix(parent_mtx, aligned_pm, twist_blend)

        pulse.nodes.connectOffsetMatrix(blend_mtx, self.twistJoint, pulse.nodes.ConnectMatrixMethod.KEEP_WORLD)

    def getParentMatrix(self, node):
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
