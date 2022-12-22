from typing import List

import pymel.core as pm

from pulse import nodes, util_nodes, joints, control_shapes
from pulse.vendor import pymetanode as meta
from pulse.core import BuildAction, BuildActionError
from pulse.core import BuildActionAttributeType as AttrType


class SplineIKFKAction(BuildAction):
    """
    Create a spline IK chain that can switch to FK.
    """

    id = "Pulse.SplineIKFK"
    display_name = "Spline IK FK"
    color = (0.4, 0.6, 0.8)
    category = "Kinematics"

    attr_definitions = [
        dict(
            name="startJoint",
            type=AttrType.NODE,
            description="The starting joint of the IK chain.",
        ),
        dict(
            name="endJoint",
            type=AttrType.NODE,
            description="The end joint of the IK chain.",
        ),
        dict(
            name="startCtl",
            type=AttrType.NODE,
            description="The start control for both IK and FK.",
        ),
        dict(
            name="midIkCtls",
            type=AttrType.NODE_LIST,
            description="The ctls to use for the spline clusters.",
        ),
        dict(
            name="endIkCtl",
            type=AttrType.NODE,
            description="The end control in IK mode.",
        ),
        dict(
            name="isStretchy",
            type=AttrType.BOOL,
            value=True,
            description="Enable stretchiness by translating bones based on the spline length.",
        ),
        dict(
            name="addPoleLine",
            type=AttrType.BOOL,
            value=True,
            description="Add a curve shape to the mid FK control that draws a line to the bone.",
        )
    ]

    def validate(self):
        if self.startJoint and self.endJoint:
            if self.endJoint not in self.startJoint.listRelatives(allDescendents=True, typ="joint"):
                self.logger.error("End joint '%s' is not a child of start joint '%s'", self.endJoint, self.startJoint)

    def run(self):
        # retrieve mid and root joints
        start_joint = self.startJoint
        end_joint = self.endJoint
        mid_joints = self._get_joint_chain(start_joint, end_joint)

        # duplicate joints for ik chain
        ik_joint_name_fmt = "{0}_ik"
        ik_jnts = nodes.duplicate_branch(start_joint, end_joint, name_fmt=ik_joint_name_fmt)
        start_ik_joint = ik_jnts[0]
        end_ik_joint = ik_jnts[-1]

        # display local rotation axes in debug mode
        if self.builder.debug:
            for jnt in ik_jnts:
                jnt.displayLocalAxis.set(True)

        # parent the joints to the start ctl
        start_ik_joint.setParent(self.startCtl)

        # setup spline ik
        num_spans = len(self.midIkCtls)
        ik_result = pm.ikHandle(
            name=f"{end_ik_joint.nodeName()}_ikHandle",
            startJoint=start_ik_joint,
            endEffector=end_ik_joint,
            solver="ikSplineSolver",
            # rootOnCurve=False,
            # createRootAxis=True,
            numSpans=num_spans + 1,
        )
        ik_handle, effector, curve = ik_result
        curve_shape: pm.nt.NurbsCurve = curve.getShape()
        # rename curve to match system
        curve.rename(f"{end_ik_joint.nodeName()}_ik_curve")
        # disable inheriting transforms on curve to prevent double translations
        curve.inheritsTransform.set(False)
        curve.translate.set(0, 0, 0)
        curve.rotate.set(0, 0, 0)
        curve.scale.set(1, 1, 1)

        # parent ik handle to the start ctl as well
        ik_handle.setParent(self.startCtl)

        if self.builder.debug:
            # show cvs when debugging
            pm.toggle(curve_shape, controlVertex=True)
        else:
            # hide curve
            curve.visibility.set(False)

        # cluster the cvs, group the first two and last two
        cv_groups = [curve_shape.cv[:1]]
        for cv in curve_shape.cv[2:-2]:
            cv_groups.append(cv)
        cv_groups.append(curve_shape.cv[-2:])

        unused_mid_ik_ctls: List = self.midIkCtls
        for i, cvs in enumerate(cv_groups):
            if i == 0:
                ik_ctl = self.startCtl
            elif i == len(cv_groups) - 1:
                ik_ctl = self.endIkCtl
            else:
                ik_ctl = self._get_closest_ctl_to_cv(cvs, unused_mid_ik_ctls)
                unused_mid_ik_ctls.remove(ik_ctl)
            cluster, cluster_handle = pm.cluster(cvs, name=f"{ik_ctl.nodeName()}_spline_ik_cluster")
            # rename shape to match cluster for debugging
            cluster_shape = cluster_handle.getShape(typ="clusterHandle")
            cluster_shape.rename(f"{cluster.nodeName()}HandleShape")
            # parent cluster handle to the ctl
            cluster_handle.setParent(ik_ctl)

        # TODO: reset curve cvs to zeros everywhere, then reset cluster pivots and transforms to be absolute
        # TODO: add bezier-handle-style offsets to 1st and 2nd-to-last cvs as desired

        # apply stretch via translate X offsets
        if self.isStretchy:
            self._setup_joint_translation_stretch(ik_jnts[1:], curve_shape)


    @staticmethod
    def _get_closest_ctl_to_cv(cv: pm.NurbsCurveCV, ctls: List[pm.nt.Transform]) -> pm.nt.Transform:
        best_ctl = None
        best_dist = None
        cv_location = pm.dt.Vector(cv.getPosition())
        for ctl in ctls:
            ctl_location = ctl.getTranslation(space="world")
            delta_location: pm.dt.Vector = (cv_location - ctl_location)
            dist = delta_location.length()
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_ctl = ctl
        return best_ctl

    @staticmethod
    def _setup_joint_translation_stretch(jnts: List[pm.PyNode], curve_shape: pm.nt.NurbsCurve):
        """
        Apply translational stretching to joints based on the length of a curve.

        Args:
            jnts: The joints to move, should not include the start joint of a spline ik chain.
            curve_shape: The curve length that is driving the stretch.
        """
        # TODO: manual stretch factor attribute
        # TODO: use un-scaled curve arc length to allow hierarchy scaling above the curve

        # create curve info node
        curve_info = pm.createNode("curveInfo", name=f"{curve_shape.nodeName()}_curveInfo")
        curve_shape.worldSpace >> curve_info.inputCurve

        # get the delta length of the curve
        rest_length = curve_info.arcLength.get()
        delta_length = util_nodes.subtract(curve_info.arcLength, rest_length)

        # divide into delta offset applied to each joint
        num = len(jnts)
        unit_delta_offset = util_nodes.divide(delta_length, num)

        for jnt in jnts:
            # add or subtract x translation, based on current value,
            # i.e. x is either pointing down bone, or in opposite direction
            if jnt.translateX.get() >= 0:
                jnt_offset = util_nodes.add(jnt.translateX.get(), unit_delta_offset)
            else:
                jnt_offset = util_nodes.subtract(jnt.translateX.get(), unit_delta_offset)
            jnt_offset >> jnt.translateX

    @staticmethod
    def _get_joint_chain(start_joint: pm.PyNode, end_joint: pm.PyNode) -> List[pm.PyNode]:
        """
        Return the chain of joints between two joints.
        """
        result = []
        parent = end_joint.getParent()
        while parent and parent != start_joint:
            if parent == start_joint:
                break
            result.append(parent)

            parent = parent.getParent()

        return list(reversed(result))
