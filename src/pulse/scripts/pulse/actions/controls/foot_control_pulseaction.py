import pymel.core as pm

import pulse.nodes
import pymetanode as meta
from pulse import utilnodes, nodes
from pulse.buildItems import BuildAction, BuildActionError
from pulse.views.contextmenus import PulseNodeContextSubMenu

try:
    import resetter
except ImportError:
    resetter = None

FOOT_BASE_CTL_METACLASSNAME = 'pulse_foot_base_ctl'
FOOT_LIFT_CTL_METACLASSNAME = 'pulse_foot_lift_ctl'
FOOT_LIFT_TOE_CTL_METACLASSNAME = 'pulse_foot_lift_toe_ctl'


class FootControlAction(BuildAction):

    def validate(self):
        if not self.ankleFollower:
            raise BuildActionError("ankleFollower is not set")
        if not self.toeFollower:
            raise BuildActionError("toeFollower is not set")
        if not self.baseControl:
            raise BuildActionError("baseControl is not set")
        if not self.liftControl:
            raise BuildActionError("liftControl is not set")
        if not self.liftToeControl:
            raise BuildActionError("liftToeControl is not set")
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

        self.baseControl.addAttr('lift', at='double', keyable=True, minValue=0, maxValue=1)
        lift = self.baseControl.attr('lift')

        self.baseControl.addAttr('roll', at='double', keyable=True)
        roll = self.baseControl.attr('roll')

        self.baseControl.addAttr('tilt', at='double', keyable=True)
        tilt = self.baseControl.attr('tilt')

        self.baseControl.addAttr('toeSwivel', at='double', keyable=True)
        toeSwivel = self.baseControl.attr('toeSwivel')

        self.baseControl.addAttr('heelSwivel', at='double', keyable=True)
        heelSwivel = self.baseControl.attr('heelSwivel')

        self.baseControl.addAttr('bendLimit', at='double', keyable=True,
                                 defaultValue=self.bendLimitDefault, minValue=0)
        bend_limit = self.baseControl.attr('bendLimit')

        self.baseControl.addAttr('straightAngle', at='double', keyable=True,
                                 defaultValue=self.straightAngleDefault, minValue=0)
        straight_angle = self.baseControl.attr('straightAngle')

        # keep evaluated Bend Limit below Straight Angle to avoid zero division and flipping problems
        clamped_bend_limit = utilnodes.min_float(bend_limit, utilnodes.subtract(straight_angle, 0.001))

        # setup hierarchy
        # ---------------

        # baseControl / heel / outerTilt / innerTilt / toe / ball
        pulse.nodes.connectOffsetMatrix(self.baseControl, self.heelPivot)
        pulse.nodes.connectOffsetMatrix(self.heelPivot, self.outerTiltPivot)
        pulse.nodes.connectOffsetMatrix(self.outerTiltPivot, self.innerTiltPivot)
        pulse.nodes.connectOffsetMatrix(self.innerTiltPivot, self.toePivot)
        pulse.nodes.connectOffsetMatrix(self.toePivot, self.ballPivot)

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

        # swivels are mostly direct
        toeSwivel >> self.toePivot.rotateZ
        heelSwivel >> self.heelPivot.rotateZ

        # inner and outer tilt simply need clamped connections
        outer_tilt = utilnodes.clamp(tilt, 0, 180)
        outer_tilt >> self.outerTiltPivot.rotateY
        inner_tilt = utilnodes.clamp(tilt, -180, 0)
        inner_tilt >> self.innerTiltPivot.rotateY

        # add lift blend
        # --------------

        # create ankle targets and matrix blend
        planted_ankle_tgt = pm.group(em=True, p=self.ankleFollower,
                                     name='{0}_anklePlanted_tgt'.format(self.ankleFollower.nodeName()))
        lifted_ankle_tgt = pm.group(em=True, p=self.ankleFollower,
                                    name='{0}_ankleLifted_tgt'.format(self.ankleFollower.nodeName()))

        pulse.nodes.connectOffsetMatrix(self.ballPivot, planted_ankle_tgt)
        pulse.nodes.connectOffsetMatrix(self.liftControl, lifted_ankle_tgt)

        lift_ankle_mtxblend = self.createMatrixBlend(planted_ankle_tgt.wm, lifted_ankle_tgt.wm, lift,
                                                     name='{0}_ankle_liftBlend'.format(self.ankleFollower.nodeName()))
        utilnodes.connectMatrix(lift_ankle_mtxblend, self.ankleFollower)

        # create toe targets and matrix blend
        planted_toe_tgt = pm.group(em=True, p=self.toeFollower,
                                   name='{0}_toePlanted_tgt'.format(self.toeFollower.nodeName()))
        lifted_toe_tgt = pm.group(em=True, p=self.toeFollower,
                                  name='{0}_toeLifted_tgt'.format(self.toeFollower.nodeName()))

        pulse.nodes.connectOffsetMatrix(self.toePivot, planted_toe_tgt)
        pulse.nodes.connectOffsetMatrix(self.liftToeControl, lifted_toe_tgt)

        lift_toe_mtxblend = self.createMatrixBlend(planted_toe_tgt.wm, lifted_toe_tgt.wm, lift,
                                                   name='{0}_toe_liftBlend'.format(self.toeFollower.nodeName()))
        utilnodes.connectMatrix(lift_toe_mtxblend, self.toeFollower)

        # lock up nodes
        # -------------

        for pivot in [self.toePivot, self.ballPivot, self.outerTiltPivot, self.innerTiltPivot, self.heelPivot]:
            pivot.v.set(False)
            for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
                attr = pivot.attr(a)
                attr.setLocked(True)
                attr.setKeyable(False)

        # re-set defaults for the new keyable attributes
        if resetter:
            resetter.setDefaults(self.baseControl)

        # setup meta data
        # ---------------

        base_ctl_data = {
            'lift_ctl': self.liftControl,
            'lift_toe_ctl': self.liftToeControl,
            'planted_ankle_tgt': planted_ankle_tgt,
            'lifted_ankle_tgt': lifted_ankle_tgt,
            'planted_toe_tgt': planted_toe_tgt,
            'lifted_toe_tgt': lifted_toe_tgt,
        }
        meta.setMetaData(self.baseControl, FOOT_BASE_CTL_METACLASSNAME, base_ctl_data)

        lift_ctl_data = {
            'base_ctl': self.baseControl
        }
        meta.setMetaData(self.liftControl, FOOT_LIFT_CTL_METACLASSNAME, lift_ctl_data)
        meta.setMetaData(self.liftToeControl, FOOT_LIFT_TOE_CTL_METACLASSNAME, lift_ctl_data)

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
    def getBaseControl(ctl: pm.PyNode):
        """
        Args:
            ctl: A base, lift, or lift-toe foot control
        """
        if meta.hasMetaClass(ctl, FOOT_BASE_CTL_METACLASSNAME):
            return ctl
        elif meta.hasMetaClass(ctl, FOOT_LIFT_CTL_METACLASSNAME):
            return meta.getMetaData(ctl, FOOT_LIFT_CTL_METACLASSNAME).get('base_ctl')
        elif meta.hasMetaClass(ctl, FOOT_LIFT_TOE_CTL_METACLASSNAME):
            return meta.getMetaData(ctl, FOOT_LIFT_TOE_CTL_METACLASSNAME).get('base_ctl')

    @staticmethod
    def snapLiftControlToAnkle(ctl: pm.PyNode):
        """
        Args:
            ctl: A foot control
        """
        base_ctl = FootControlUtils.getBaseControl(ctl)
        if not base_ctl:
            pm.warning(f"Couldn't get foot base control from: {ctl}")
            return

        base_ctl_data = meta.getMetaData(base_ctl, FOOT_BASE_CTL_METACLASSNAME)
        lift_ctl = base_ctl_data.get('lift_ctl')
        planted_ankle_tgt = base_ctl_data.get('planted_ankle_tgt')

        if not lift_ctl:
            pm.warning(f"Couldn't get foot lift control from base ctl: {base_ctl}")
            return

        if not planted_ankle_tgt:
            pm.warning(f"Couldn't get foot planted ankle target from base ctl: {base_ctl}")
            return

        mtx = planted_ankle_tgt.wm.get()
        mtx.scale = (1, 1, 1)
        nodes.setWorldMatrix(lift_ctl, mtx)

    @staticmethod
    def setLift(ctl: pm.PyNode, lift: float):
        """
        Args:
            ctl: A foot control
            lift: The amount of lift (0..1)
        """
        base_ctl = FootControlUtils.getBaseControl(ctl)
        if not base_ctl:
            pm.warning(f"Couldn't get foot base control from: {ctl}")
            return

        base_ctl.attr('lift').set(lift)

    @staticmethod
    def liftFoot(ctl: pm.PyNode):
        """
        Snap the lift control to the ankle, and then set lift to 1

        Args:
            ctl: A foot control
        """
        FootControlUtils.snapLiftControlToAnkle(ctl)
        FootControlUtils.setLift(ctl, 1)

    @staticmethod
    def plantFoot(ctl: pm.PyNode):
        """
        Set lift to 0

        Args:
            ctl: A foot control
        """
        FootControlUtils.setLift(ctl, 0)


class FootControlContextSubMenu(PulseNodeContextSubMenu):
    """
    Context menu for snapping a lift control to the current position of the planted ankle.
    """

    @classmethod
    def shouldBuildSubMenu(cls, menu) -> bool:
        return cls.isNodeWithMetaClassSelected(
            FOOT_BASE_CTL_METACLASSNAME,
            FOOT_LIFT_CTL_METACLASSNAME,
            FOOT_LIFT_TOE_CTL_METACLASSNAME
        )

    def buildMenuItems(self):
        pm.menuItem(l='Snap To Ankle', rp=self.getSafeRadialPosition('S'), c=pm.Callback(self.snapToAnkleForSelected))
        pm.menuItem(l='Lift', rp=self.getSafeRadialPosition('NE'), c=pm.Callback(self.setFootLiftedForSelected, True))
        pm.menuItem(l='Plant', rp=self.getSafeRadialPosition('SE'), c=pm.Callback(self.setFootLiftedForSelected, False))

    def snapToAnkleForSelected(self):
        sel_ctls = self.getSelectedNodesWithMetaClass(
            FOOT_BASE_CTL_METACLASSNAME,
            FOOT_LIFT_CTL_METACLASSNAME,
            FOOT_LIFT_TOE_CTL_METACLASSNAME
        )
        for ctl in sel_ctls:
            FootControlUtils.snapLiftControlToAnkle(ctl)

    def setFootLiftedForSelected(self, lifted: bool):
        sel_ctls = self.getSelectedNodesWithMetaClass(
            FOOT_BASE_CTL_METACLASSNAME,
            FOOT_LIFT_CTL_METACLASSNAME,
            FOOT_LIFT_TOE_CTL_METACLASSNAME
        )
        for ctl in sel_ctls:
            if lifted:
                FootControlUtils.liftFoot(ctl)
            else:
                FootControlUtils.plantFoot(ctl)
