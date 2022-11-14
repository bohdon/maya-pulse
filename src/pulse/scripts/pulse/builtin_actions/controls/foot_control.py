import pymel.core as pm

from pulse.vendor import pymetanode as meta
from pulse import util_nodes, nodes
from pulse.core import BuildAction, BuildActionError
from pulse.core import BuildActionAttributeType as AttrType
from pulse.ui.contextmenus import PulseNodeContextSubMenu

FOOT_CTL_METACLASSNAME = "pulse_foot_ctl"


class FootControlAction(BuildAction):
    """
    Create a classic attribute-driven foot roll and tilt control.
    """

    id = "Pulse.FootControl"
    display_name = "Foot Control"
    color = (0.85, 0.65, 0.4)
    category = "Controls"

    attr_definitions = [
        dict(
            name="ankleFollower",
            type=AttrType.NODE,
            description="The follower node representing the ankle of the foot",
        ),
        dict(
            name="toeFollower",
            type=AttrType.NODE,
            description="The follower node representing the toe of the foot",
        ),
        dict(
            name="control",
            type=AttrType.NODE,
            description="The control to use as the parent for the foot systems and attributes.",
        ),
        dict(
            name="toePivot",
            type=AttrType.NODE,
            description="The toe pivot locator for rolling the foot",
        ),
        dict(
            name="ballPivot",
            type=AttrType.NODE,
            description="The ball pivot locator for rolling the foot",
        ),
        dict(
            name="outerTiltPivot",
            type=AttrType.NODE,
            description="The outer pivot locator for tilting the foot",
        ),
        dict(
            name="innerTiltPivot",
            type=AttrType.NODE,
            description="The inner pivot locator for tilting the foot",
        ),
        dict(
            name="heelPivot",
            type=AttrType.NODE,
            description="The heel pivot locator for rolling the foot",
        ),
        dict(
            name="bendLimitDefault",
            type=AttrType.FLOAT,
            value=50,
            description="The default value for the Bend Limit attribute",
        ),
        dict(
            name="straightAngleDefault",
            type=AttrType.FLOAT,
            value=70,
            description="The default value for the Straight Angle attribute",
        ),
        dict(
            name="ballControl",
            type=AttrType.NODE,
            optional=True,
            description="The optional control that drives the ball joint. "
            "Used only in meta data so that it can be found by utils.",
        ),
        dict(
            name="extraControls",
            type=AttrType.NODE_LIST,
            optional=True,
            description="Extra controls that should be marked for use with foot control utils",
        ),
    ]

    def run(self):
        # add attrs
        # ---------

        self.control.addAttr("roll", attributeType="double", keyable=True)
        roll = self.control.attr("roll")

        self.control.addAttr("tilt", attributeType="double", keyable=True)
        tilt = self.control.attr("tilt")

        self.control.addAttr("toeSwivel", attributeType="double", keyable=True)
        toe_swivel = self.control.attr("toeSwivel")

        self.control.addAttr("heelSwivel", attributeType="double", keyable=True)
        heel_swivel = self.control.attr("heelSwivel")

        self.control.addAttr(
            "bendLimit", attributeType="double", keyable=True, minValue=0, defaultValue=self.bendLimitDefault
        )
        bend_limit = self.control.attr("bendLimit")

        self.control.addAttr(
            "straightAngle", attributeType="double", keyable=True, minValue=0, defaultValue=self.straightAngleDefault
        )
        straight_angle = self.control.attr("straightAngle")

        # keep evaluated Bend Limit below Straight Angle to avoid zero division and flipping problems
        clamped_bend_limit = util_nodes.min_float(bend_limit, util_nodes.subtract(straight_angle, 0.001))

        # setup hierarchy
        # ---------------

        # control > heel > outerTilt > innerTilt > toe > ball
        offset_connect_method = nodes.ConnectMatrixMethod.CREATE_OFFSET
        nodes.connect_matrix(self.control.wm, self.heelPivot, offset_connect_method)
        nodes.connect_matrix(self.heelPivot.wm, self.outerTiltPivot, offset_connect_method)
        nodes.connect_matrix(self.outerTiltPivot.wm, self.innerTiltPivot, offset_connect_method)
        nodes.connect_matrix(self.innerTiltPivot.wm, self.toePivot, offset_connect_method)
        nodes.connect_matrix(self.toePivot.wm, self.ballPivot, offset_connect_method)

        # ballPivot > ankleFollower
        nodes.connect_matrix(self.ballPivot.wm, self.ankleFollower, offset_connect_method)

        # toePivot > toeFollower
        nodes.connect_matrix(self.toePivot.wm, self.toeFollower, offset_connect_method)

        # calculate custom foot attrs
        # ---------------------------

        # drive heel rotation with negative footRoll
        heel_roll = util_nodes.clamp(roll, -180, 0)
        heel_roll >> self.heelPivot.rotateX

        # get percentage blend between 0..BendLimit and BendLimit..StraightAngle
        zero_to_bend_pct = util_nodes.set_range(roll, 0, 1, 0, clamped_bend_limit)
        bend_to_toe_pct = util_nodes.set_range(roll, 0, 1, clamped_bend_limit, straight_angle)

        # multiply pcts to get ball rotation curve that goes up towards BendLimit,
        # then back down towards StraightAngle
        neg_bend_to_toe_pct = util_nodes.reverse(bend_to_toe_pct)
        ball_roll_factor = util_nodes.multiply(zero_to_bend_pct, neg_bend_to_toe_pct)
        ball_roll = util_nodes.multiply(ball_roll_factor, clamped_bend_limit)
        ball_roll >> self.ballPivot.rotateX

        # multiply bend pct to get toe rotation coming from bend, then
        # add in extra rotation to add after straight angle is reached, so that foot roll isn't clamped
        toe_roll_from_blend = util_nodes.multiply(bend_to_toe_pct, straight_angle)
        toe_roll_excess = util_nodes.clamp(util_nodes.subtract(roll, straight_angle), 0, 180)
        toe_roll = util_nodes.add(toe_roll_from_blend, toe_roll_excess)
        toe_roll >> self.toePivot.rotateX

        # TODO: mirror swivel values (since roll cannot be flipped, we can't just re-orient the pivot nodes)

        # swivels are mostly direct, toe swivel positive values should move the heel outwards
        util_nodes.multiply(toe_swivel, -1) >> self.toePivot.rotateZ
        heel_swivel >> self.heelPivot.rotateZ

        # inner and outer tilt simply need clamped connections
        outer_tilt = util_nodes.clamp(tilt, 0, 180)
        outer_tilt >> self.outerTiltPivot.rotateY
        inner_tilt = util_nodes.clamp(tilt, -180, 0)
        inner_tilt >> self.innerTiltPivot.rotateY

        # lock up nodes
        # -------------

        for pivot in [self.toePivot, self.ballPivot, self.outerTiltPivot, self.innerTiltPivot, self.heelPivot]:
            pivot.v.set(False)
            for a in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
                attr = pivot.attr(a)
                attr.setLocked(True)
                attr.setKeyable(False)

        # setup meta data
        # ---------------

        foot_ctl_data = {
            "foot_ctl": self.control,
            "ball_ctl": self.ballControl,
            "ankle_follower": self.ankleFollower,
            "toe_follower": self.toeFollower,
        }

        meta_nodes = {self.control, self.ballControl}
        meta_nodes.update(self.extraControls)
        for node in meta_nodes:
            meta.set_metadata(node, FOOT_CTL_METACLASSNAME, foot_ctl_data)


class FootControlUtils(object):
    @staticmethod
    def get_foot_ctl_data(ctl):
        return meta.get_metadata(ctl, FOOT_CTL_METACLASSNAME)

    @staticmethod
    def get_foot_ctl(ctl: pm.PyNode):
        """
        Return the main foot control for a foot control system

        Args:
            ctl: A control with foot control metadata
        """
        if meta.has_metaclass(ctl, FOOT_CTL_METACLASSNAME):
            return meta.get_metadata(ctl, FOOT_CTL_METACLASSNAME).get("foot_ctl")

    @staticmethod
    def lift_foot(ctl: pm.PyNode):
        """
        Snap the lift control to the ankle, and then set lift to 1

        Args:
            ctl: A foot control
        """
        ctl_data = FootControlUtils.get_foot_ctl_data(ctl)
        if not ctl_data:
            pm.warning(f"Couldn't get foot control data from: {ctl}")

        foot_ctl = ctl_data.get("foot_ctl")
        if not foot_ctl:
            pm.warning(f"Foot control meta data is missing foot control: {ctl_data}")
            return

        ankle_follower = ctl_data.get("ankle_follower")
        if not ankle_follower:
            pm.warning(f"Foot control meta data is missing ankle follower: {ctl_data}")
            return

        # get optional ball ctl, if set, we can match ball rotations
        ball_ctl = ctl_data.get("ball_ctl")
        toe_follower = ctl_data.get("toe_follower")
        if ball_ctl and toe_follower:
            # store toe mtx now, then restore it after everything's been updated
            toe_mtx = toe_follower.wm.get()

        # move foot control to current ankle position
        ankle_mtx = ankle_follower.wm.get()
        ankle_mtx.scale = (1, 1, 1)
        nodes.set_world_matrix(foot_ctl, ankle_mtx)

        # clear foot control values to ensure no extra transformations are in effect
        foot_ctl.attr("roll").set(0)
        foot_ctl.attr("tilt").set(0)
        foot_ctl.attr("toeSwivel").set(0)
        foot_ctl.attr("heelSwivel").set(0)

        if ball_ctl and toe_follower:
            # update ball ctl rotation to match last known rotation
            nodes.set_world_matrix(ball_ctl, toe_mtx, translate=False, rotate=True, scale=False)


class FootControlContextSubMenu(PulseNodeContextSubMenu):
    """
    Context menu for working with foot controls
    """

    @classmethod
    def should_build_sub_menu(cls, menu) -> bool:
        return cls.is_node_with_metaclass_selected(FOOT_CTL_METACLASSNAME)

    def build_menu_items(self):
        pm.menuItem(
            label="Lift",
            radialPosition=self.get_safe_radial_position("NE"),
            command=pm.Callback(self.lift_foot_for_selected),
        )

    def lift_foot_for_selected(self):
        sel_ctls = self.get_selected_nodes_with_meta_class(FOOT_CTL_METACLASSNAME)
        for ctl in sel_ctls:
            FootControlUtils.lift_foot(ctl)
