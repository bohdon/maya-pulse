from typing import List

from maya import cmds
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
            name="fkCtls",
            type=AttrType.NODE_LIST,
            description="The ctls to use for each joint in FK mode.",
        ),
        dict(
            name="isStretchy",
            type=AttrType.BOOL,
            value=True,
            description="Enable stretchiness by translating bones based on the spline length.",
        ),
    ]

    def validate(self):
        if self.startJoint and self.endJoint:
            if self.endJoint not in self.startJoint.listRelatives(allDescendents=True, typ="joint"):
                self.logger.error("End joint '%s' is not a child of start joint '%s'", self.endJoint, self.startJoint)

    def run(self):
        # retrieve mid and root joints
        start_jnt = self.startJoint
        end_jnt = self.endJoint
        mid_jnts = self._get_joint_chain(start_jnt, end_jnt)
        target_jnts: List[pm.nt.Joint] = [start_jnt] + mid_jnts[:] + [end_jnt]
        self.logger.debug(f"target_jnts: {target_jnts}")

        # setup ik chain
        ik_jnts = self._setup_ik_chain(start_jnt, end_jnt)
        ik_ctls = [self.endIkCtl] + self.midIkCtls
        # use the end ik control directly when connecting to end joint so that rotation is explicit
        ik_leaders = ik_jnts[:-1] + [self.endIkCtl]
        self.logger.debug(f"ik_leaders: {ik_leaders}")

        # setup fk chain
        # include root ctl as one of the fk controls
        fk_ctls = self._get_closest_ctls(target_jnts, [self.startCtl] + self.fkCtls)
        self.logger.debug(f"fk_ctls: {fk_ctls}")

        ik_attr = self._setup_ikfk_switch(target_jnts, ik_leaders, fk_ctls)

        # connect visibility
        if not self.builder.debug:
            for ik_ctl in ik_ctls:
                ik_ctl.v.setLocked(False)
                ik_attr >> ik_ctl.v
                ik_ctl.v.setLocked(True)

            fk_attr = util_nodes.reverse(ik_attr)
            for fk_ctl in self.fkCtls:
                fk_ctl.v.setLocked(False)
                fk_attr >> fk_ctl.v
                fk_ctl.v.setLocked(True)

    def _setup_ik_chain(self, start_jnt: pm.nt.Joint, end_jnt: pm.nt.Joint):

        # duplicate joints for ik chain
        ik_joint_name_fmt = "{0}_ik"
        ik_jnts = nodes.duplicate_branch(start_jnt, end_jnt, name_fmt=ik_joint_name_fmt)
        start_ik_joint = ik_jnts[0]
        end_ik_joint = ik_jnts[-1]

        # display local rotation axes in debug mode
        if self.builder.debug:
            for jnt in ik_jnts:
                jnt.displayLocalAxis.set(True)
        else:
            start_ik_joint.visibility.set(False)

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
            # hide curve and ik
            curve.visibility.set(False)
            ik_handle.visibility.set(False)

        # cluster the cvs, group the first two and last two
        cv_groups = [curve_shape.cv[:1]]
        for cv in curve_shape.cv[2:-2]:
            cv_groups.append(cv)
        cv_groups.append(curve_shape.cv[-2:])

        unused_mid_ik_ctls: List = self.midIkCtls[:]
        for i, cv in enumerate(cv_groups):
            if i == 0:
                ik_ctl = self.startCtl
            elif i == len(cv_groups) - 1:
                ik_ctl = self.endIkCtl
            else:
                cv_location = pm.dt.Vector(cv.getPosition())
                ik_ctl = self._get_closest_ctl_to_location(cv_location, unused_mid_ik_ctls)
                unused_mid_ik_ctls.remove(ik_ctl)
            cluster, cluster_handle = pm.cluster(cv, name=f"{ik_ctl.nodeName()}_spline_ik_cluster")
            # rename shape to match cluster for debugging
            cluster_shape = cluster_handle.getShape(typ="clusterHandle")
            cluster_shape.rename(f"{cluster.nodeName()}HandleShape")
            # parent cluster handle to the ctl
            cluster_handle.setParent(ik_ctl)

            if not self.builder.debug:
                cluster_handle.visibility.set(False)

        # TODO: reset curve cvs to zeros everywhere, then reset cluster pivots and transforms to be absolute
        # TODO: add bezier-handle-style offsets to 1st and 2nd-to-last cvs as desired

        # apply stretch via translate X offsets
        if self.isStretchy:
            delta_length = self._setup_joint_translation_stretch(ik_jnts[1:], curve_shape)
            self.endIkCtl.addAttr("stretchDelta", attributeType="double", keyable=False)
            delta_length >> self.endIkCtl.stretchDelta
            cmds.setAttr(f"{self.endIkCtl}.stretchDelta", edit=True, lock=True, channelBox=True)

        return ik_jnts

    def _setup_ikfk_switch(
        self, target_jnts: List[pm.nt.Joint], ik_leaders: List[pm.nt.Transform], fk_leaders: List[pm.nt.Transform]
    ):
        if len(target_jnts) != len(ik_leaders):
            raise ValueError("ik_leaders is not the same length as target_jnts")
        if len(target_jnts) != len(fk_leaders):
            raise ValueError("fk_leaders is not the same length as target_jnts")

        # add ikfk switch attr (integer, not blend)
        self.startCtl.addAttr("ik", min=0, max=1, attributeType="short", defaultValue=1, keyable=1)
        ik_attr = self.startCtl.attr("ik")

        # create and connect ik / fk matrix choice nodes
        for ik_leader, fk_leader, target_jnt in zip(ik_leaders, fk_leaders, target_jnts):
            choice = util_nodes.choice(ik_attr, fk_leader.wm, ik_leader.wm)
            choice.node().rename(f"{target_jnt.nodeName()}_ikfk_choice")
            nodes.connect_matrix(choice, target_jnt, nodes.ConnectMatrixMethod.SNAP)

        return ik_attr

    @staticmethod
    def _get_closest_ctls(targets: List[pm.nt.Transform], ctls: List[pm.nt.Transform]) -> List[pm.nt.Transform]:
        """
        Return the closest control for each node in targets.
        """
        result = []
        for target in targets:
            location = target.getTranslation(space="world")
            ctl = SplineIKFKAction._get_closest_ctl_to_location(location, ctls)
            result.append(ctl)
        return result

    @staticmethod
    def _get_closest_ctl_to_location(location: pm.dt.Vector, ctls: List[pm.nt.Transform]) -> pm.nt.Transform:
        best_ctl = None
        best_dist = None
        for ctl in ctls:
            ctl_location = ctl.getTranslation(space="world")
            delta_location: pm.dt.Vector = location - ctl_location
            dist = delta_location.length()
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_ctl = ctl
        return best_ctl

    @staticmethod
    def _setup_joint_translation_stretch(jnts: List[pm.PyNode], curve_shape: pm.nt.NurbsCurve) -> pm.Attribute:
        """
        Apply translational stretching to joints based on the length of a curve.

        Args:
            jnts: The joints to move, should not include the start joint of a spline ik chain.
            curve_shape: The curve length that is driving the stretch.

        Returns:
            An output attribute that represents the delta length of the curve compared to its rest length.
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

        return delta_length

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
