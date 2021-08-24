import pymel.core as pm

import pulse.nodes
import pymetanode as meta
from pulse import utilnodes, nodes
from pulse.buildItems import BuildAction, BuildActionError
from pulse.views.contextmenus import PulseNodeContextSubMenu

FOOT_CTL_METACLASSNAME = 'pulse_foot_ctl'


class FootControlAction(BuildAction):

    def validate(self):
        if not self.ankleFollower:
            raise BuildActionError("ankleFollower is not set")
        if not self.toeFollower:
            raise BuildActionError("toeFollower is not set")
        if not self.control:
            raise BuildActionError("control is not set")
        if not self.toePivot:
            raise BuildActionError("toePivot is not set")
        if not self.ballPivot:
            raise BuildActionError("ballPivot is not set")
        if not self.outerTiltPivot:
            raise BuildActionError("outerTiltPivot is not set")
        if not self.innerTiltPivot:
            raise BuildActionError("innerTiltPivot is not set")
        if not self.heelPivot:
            raise BuildActionError("heelPivot is not set")

    def run(self):
        # add attrs
        # ---------

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

        # setup hierarchy
        # ---------------

        # control > heel > outerTilt > innerTilt > toe > ball
        offset_connect_method = pulse.nodes.ConnectMatrixMethod.CREATE_OFFSET
        pulse.nodes.connectMatrix(self.control.wm, self.heelPivot, offset_connect_method)
        pulse.nodes.connectMatrix(self.heelPivot.wm, self.outerTiltPivot, offset_connect_method)
        pulse.nodes.connectMatrix(self.outerTiltPivot.wm, self.innerTiltPivot, offset_connect_method)
        pulse.nodes.connectMatrix(self.innerTiltPivot.wm, self.toePivot, offset_connect_method)
        pulse.nodes.connectMatrix(self.toePivot.wm, self.ballPivot, offset_connect_method)

        # ballPivot > ankleFollower
        pulse.nodes.connectMatrix(self.ballPivot.wm, self.ankleFollower, offset_connect_method)

        # toePivot > toeFollower
        pulse.nodes.connectMatrix(self.toePivot.wm, self.toeFollower, offset_connect_method)

        # calculate custom foot attrs
        # ---------------------------

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

        # TODO: mirror swivel values (since roll cannot be flipped, we can't just re-orient the pivot nodes)

        # swivels are mostly direct, toe swivel positive values should move the heel outwards
        utilnodes.multiply(toeSwivel, -1) >> self.toePivot.rotateZ
        heelSwivel >> self.heelPivot.rotateZ

        # inner and outer tilt simply need clamped connections
        outer_tilt = utilnodes.clamp(tilt, 0, 180)
        outer_tilt >> self.outerTiltPivot.rotateY
        inner_tilt = utilnodes.clamp(tilt, -180, 0)
        inner_tilt >> self.innerTiltPivot.rotateY

        # lock up nodes
        # -------------

        for pivot in [self.toePivot, self.ballPivot, self.outerTiltPivot, self.innerTiltPivot, self.heelPivot]:
            pivot.v.set(False)
            for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
                attr = pivot.attr(a)
                attr.setLocked(True)
                attr.setKeyable(False)

        # setup meta data
        # ---------------

        foot_ctl_data = {
            'foot_ctl': self.control,
            'ball_ctl': self.ballControl,
            'ankle_follower': self.ankleFollower,
            'toe_follower': self.toeFollower,
        }

        meta_nodes = {self.control, self.ballControl}
        meta_nodes.update(self.extraControls)
        for node in meta_nodes:
            meta.setMetaData(node, FOOT_CTL_METACLASSNAME, foot_ctl_data)

    def createMatrixBlend(self, mtxA, mtxB, blendAttr, name):
        """
        Create a util node to blend between two matrices.

        Args:
            mtxA (Attribute): Matrix attribute to use when blendAttr is 0
            mtxB (Attribute): Matrix attribute to use when blendAttr is 1
            blendAttr (Attribute): Float attribute to blend between the matrices
            name (str): The name of the new node

        Returns:
            The blended output attr of the node that was created
        """
        blendNode = pm.createNode('wtAddMatrix', n=name)

        mtxA >> blendNode.wtMatrix[0].matrixIn
        utilnodes.reverse(blendAttr) >> blendNode.wtMatrix[0].weightIn

        mtxB >> blendNode.wtMatrix[1].matrixIn
        blendAttr >> blendNode.wtMatrix[1].weightIn

        return blendNode.matrixSum


class FootControlUtils(object):

    @staticmethod
    def getFootControlData(ctl):
        return meta.getMetaData(ctl, FOOT_CTL_METACLASSNAME)

    @staticmethod
    def getFootControl(ctl: pm.PyNode):
        """
        Return the main foot control for a foot control system

        Args:
            ctl: A control with foot control meta data
        """
        if meta.hasMetaClass(ctl, FOOT_CTL_METACLASSNAME):
            return meta.getMetaData(ctl, FOOT_CTL_METACLASSNAME).get('foot_ctl')

    @staticmethod
    def liftFoot(ctl: pm.PyNode):
        """
        Snap the lift control to the ankle, and then set lift to 1

        Args:
            ctl: A foot control
        """
        ctl_data = FootControlUtils.getFootControlData(ctl)
        if not ctl_data:
            pm.warning(f"Couldn't get foot control data from: {ctl}")

        foot_ctl = ctl_data.get('foot_ctl')
        if not foot_ctl:
            pm.warning(f"Foot control meta data is missing foot control: {ctl_data}")
            return

        ankle_follower = ctl_data.get('ankle_follower')
        if not ankle_follower:
            pm.warning(f"Foot control meta data is missing ankle follower: {ctl_data}")
            return

        # get optional ball ctl, if set, we can match ball rotations
        ball_ctl = ctl_data.get('ball_ctl')
        toe_follower = ctl_data.get('toe_follower')
        if ball_ctl and toe_follower:
            # store toe mtx now, then restore it after everythings been  updated
            toe_mtx = toe_follower.wm.get()

        # move foot control to current ankle position
        ankle_mtx = ankle_follower.wm.get()
        ankle_mtx.scale = (1, 1, 1)
        nodes.setWorldMatrix(foot_ctl, ankle_mtx)

        # clear foot control values to ensure no extra transformations are in effect
        foot_ctl.attr('roll').set(0)
        foot_ctl.attr('tilt').set(0)
        foot_ctl.attr('toeSwivel').set(0)
        foot_ctl.attr('heelSwivel').set(0)

        if ball_ctl and toe_follower:
            # update ball ctl rotation to match last known rotation
            nodes.setWorldMatrix(ball_ctl, toe_mtx, translate=False, rotate=True, scale=False)


class FootControlContextSubMenu(PulseNodeContextSubMenu):
    """
    Context menu for working with foot controls
    """

    @classmethod
    def shouldBuildSubMenu(cls, menu) -> bool:
        return cls.isNodeWithMetaClassSelected(FOOT_CTL_METACLASSNAME)

    def buildMenuItems(self):
        pm.menuItem(l='Lift', rp=self.getSafeRadialPosition('NE'), c=pm.Callback(self.liftFootForSelected))

    def liftFootForSelected(self):
        sel_ctls = self.getSelectedNodesWithMetaClass(FOOT_CTL_METACLASSNAME)
        for ctl in sel_ctls:
            FootControlUtils.liftFoot(ctl)
