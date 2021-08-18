import pulse
import pulse.nodes
from pulse import utilnodes

FOOT_CTL_METACLASSNAME = 'pulse_foot_ctl'


class FootControlAction(pulse.BuildAction):

    def validate(self):
        if not self.control:
            raise pulse.BuildActionError("follower is not set")
        if not self.toePivot:
            raise pulse.BuildActionError("toePivot is not set")
        if not self.ballPivot:
            raise pulse.BuildActionError("ballPivot is not set")
        if not self.heelPivot:
            raise pulse.BuildActionError("heelPivot is not set")

    def run(self):
        self.control.addAttr('footRoll', at='double', keyable=True)
        foot_roll = self.control.attr('footRoll')

        self.control.addAttr('bendLimit', at='double', keyable=True, defaultValue=self.bendLimitDefault)
        bend_limit = self.control.attr('bendLimit')

        self.control.addAttr('straightAngle', at='double', keyable=True, defaultValue=self.straightAngleDefault)
        straight_angle = self.control.attr('straightAngle')

        pulse.nodes.connectOffsetMatrix(self.heelPivot, self.toePivot)
        pulse.nodes.connectOffsetMatrix(self.toePivot, self.ballPivot)

        # drive heel locator rotation with negative footRoll
        heel_roll = utilnodes.clamp(foot_roll, -180, 0)
        heel_roll >> self.heelPivot.rotateX

        # get percentage blend between 0..BendLimit and BendLimit..StraightAngle
        zero_to_bend_pct = utilnodes.setRange(foot_roll, 0, 1, 0, bend_limit)
        bend_to_toe_pct = utilnodes.setRange(foot_roll, 0, 1, bend_limit, straight_angle)

        # multiply pcts to get ball rotation curve that goes up towards BendLimit,
        # then back down towards StraightAngle
        neg_bend_to_toe_pct = utilnodes.reverse(bend_to_toe_pct)
        ball_roll_factor = utilnodes.multiply(zero_to_bend_pct, neg_bend_to_toe_pct)
        ball_roll = utilnodes.multiply(ball_roll_factor, bend_limit)
        ball_roll >> self.ballPivot.rotateX

        # multiply bend pct to get toe rotation coming from bend, then
        # add in extra rotation to add after straight angle is reached, so that foot roll isn't clamped
        toe_roll_from_blend = utilnodes.multiply(bend_to_toe_pct, straight_angle)
        toe_roll_excess = utilnodes.clamp(utilnodes.subtract(foot_roll, straight_angle), 0, 180)
        toe_roll = utilnodes.add(toe_roll_from_blend, toe_roll_excess)
        toe_roll >> self.toePivot.rotateX
