import pulse
import pulse.nodes
from pulse import utilnodes

try:
    import resetter
except ImportError:
    resetter = None

FOOT_CTL_METACLASSNAME = 'pulse_foot_ctl'


class FootControlAction(pulse.BuildAction):

    def validate(self):
        if not self.control:
            raise pulse.BuildActionError("follower is not set")
        if not self.toePivot:
            raise pulse.BuildActionError("toePivot is not set")
        if not self.ballPivot:
            raise pulse.BuildActionError("ballPivot is not set")
        if not self.outerTiltPivot:
            raise pulse.BuildActionError("outerTiltPivot is not set")
        if not self.innerTiltPivot:
            raise pulse.BuildActionError("innerTiltPivot is not set")
        if not self.heelPivot:
            raise pulse.BuildActionError("heelPivot is not set")

    def run(self):
        self.control.addAttr('roll', at='double', keyable=True)
        roll = self.control.attr('roll')

        self.control.addAttr('tilt', at='double', keyable=True)
        tilt = self.control.attr('tilt')

        self.control.addAttr('toeSwivel', at='double', keyable=True)
        toeSwivel = self.control.attr('toeSwivel')

        self.control.addAttr('heelSwivel', at='double', keyable=True)
        heelSwivel = self.control.attr('heelSwivel')

        self.control.addAttr('bendLimit', at='double', keyable=True,
                             defaultValue=self.bendLimitDefault, minValue=0)
        bend_limit = self.control.attr('bendLimit')

        self.control.addAttr('straightAngle', at='double', keyable=True,
                             defaultValue=self.straightAngleDefault, minValue=0)
        straight_angle = self.control.attr('straightAngle')

        # keep evaluated Bend Limit below Straight Angle to avoid zero division and flipping problems
        clamped_bend_limit = utilnodes.min_float(bend_limit, utilnodes.subtract(straight_angle, 0.001))

        # heel > outerTilt > innerTilt > toe > ball
        pulse.nodes.connectOffsetMatrix(self.heelPivot, self.outerTiltPivot)
        pulse.nodes.connectOffsetMatrix(self.outerTiltPivot, self.innerTiltPivot)
        pulse.nodes.connectOffsetMatrix(self.innerTiltPivot, self.toePivot)
        pulse.nodes.connectOffsetMatrix(self.toePivot, self.ballPivot)

        # drive heel rotation with negative footRoll
        heel_roll = utilnodes.clamp(roll, -180, 0)
        heel_roll >> self.heelPivot.rotateX

        # get percentage blend between 0..BendLimit and BendLimit..StraightAngle
        zero_to_bend_pct = utilnodes.setRange(roll, 0, 1, 0, clamped_bend_limit)
        bend_to_toe_pct = utilnodes.setRange(roll, 0, 1, clamped_bend_limit, straight_angle)

        # multiply pcts to get ball rotation curve that goes up towards BendLimit,
        # then back down towards StraightAngle
        neg_bend_to_toe_pct = utilnodes.reverse(bend_to_toe_pct)
        ball_roll_factor = utilnodes.multiply(zero_to_bend_pct, neg_bend_to_toe_pct)
        ball_roll = utilnodes.multiply(ball_roll_factor, clamped_bend_limit)
        ball_roll >> self.ballPivot.rotateX

        # multiply bend pct to get toe rotation coming from bend, then
        # add in extra rotation to add after straight angle is reached, so that foot roll isn't clamped
        toe_roll_from_blend = utilnodes.multiply(bend_to_toe_pct, straight_angle)
        toe_roll_excess = utilnodes.clamp(utilnodes.subtract(roll, straight_angle), 0, 180)
        toe_roll = utilnodes.add(toe_roll_from_blend, toe_roll_excess)
        toe_roll >> self.toePivot.rotateX

        # swivels are mostly direct
        toeSwivel >> self.toePivot.rotateZ
        heelSwivel >> self.heelPivot.rotateZ

        # inner and outer tilt simply need clamped connections
        outer_tilt = utilnodes.clamp(tilt, 0, 180)
        outer_tilt >> self.outerTiltPivot.rotateY
        inner_tilt = utilnodes.clamp(tilt, -180, 0)
        inner_tilt >> self.innerTiltPivot.rotateY

        if resetter:
            resetter.setDefaultsForAttrs([roll, tilt, toeSwivel, heelSwivel, bend_limit, straight_angle])
