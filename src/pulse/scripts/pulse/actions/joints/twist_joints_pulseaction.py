import pymel.core as pm

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

        # get parent world matrix
        parent_mtx = self.getParentMatrix(self.twistJoint)

        if self.alignToRestPose:
            # calculate the resting position of the align joint, including joint orients
            jo_matrix = pulse.utilnodes.composeMatrix(rotate=self.alignJoint.jo)
            align_tgt_mtx = pulse.utilnodes.multMatrix(jo_matrix, self.alignJoint.parentMatrix)
        else:
            # use the align joint world matrix directly
            align_tgt_mtx = self.alignJoint.wm

        # create aligned version of the parent matrix
        aligned_pm = pulse.utilnodes.alignMatrixToDirection(parent_mtx, self.forwardAxis, self.alignAxis,
                                                            self.alignAxis, align_tgt_mtx)

        # blend aligned matrix with default parent matrix
        blend_mtx = pulse.utilnodes.blendMatrix(parent_mtx, aligned_pm, twist_blend)

        # TODO: what if offsetParentMatrix is already connected? how do we incorporate it as the new parent matrix?
        blend_mtx >> self.twistJoint.offsetParentMatrix
        self.twistJoint.inheritsTransform.set(False)

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
