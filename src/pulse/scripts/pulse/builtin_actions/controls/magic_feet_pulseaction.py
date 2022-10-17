import pymel.core as pm

import pulse.nodes
import pulse.utilnodes
from pulse.vendor import pymetanode as meta
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType

MAGIC_FEET_CTL_METACLASSNAME = 'pulse_magicfeet_ctl'
MAGIC_FEET_LIFT_CTL_METACLASSNAME = 'pulse_magicfeet_lift_ctl'


class MagicFeetAction(BuildAction):
    id = 'Pulse.MagicFeet'
    display_name = 'Magic Feet'
    description = 'Allows controlling foot rotation, blending pivots between toe, heel and ankle'
    color = (.85, .65, .4)
    category = 'Controls'

    _offsetName = '{0}_magic'

    attr_definitions = [
        dict(name='follower', type=AttrType.NODE,
             description="The control to drive with the final foot location."),
        dict(name='toeFollower', type=AttrType.NODE,
             description="The toe control to drive with the final toe location."),
        dict(name='createFollowerOffset', type=AttrType.OPTION, value=1, options=['Always', 'Exclude Joints'],
             description="Creates and constrains a parent transform for the follower node, "
                         "instead of constraining the follower itself."),
        dict(name='control', type=AttrType.NODE, description="The magic feet control."),
        dict(name='liftControl', type=AttrType.NODE, description="The control to use when the foot is lifted."),
        dict(name='toePivot', type=AttrType.NODE, description="Node where the ball should pivot."),
        dict(name='plantedTarget', type=AttrType.NODE,
             description="The transform to use as the planted target location, will be created if not given, "
                         "allows creating a selectable node with custom shape."),
    ]

    def validate(self):
        if not self.follower:
            raise BuildActionError("follower is not set")
        if not self.toeFollower:
            raise BuildActionError("toeFollower is not set")
        if not self.control:
            raise BuildActionError("control is not set")
        if not self.liftControl:
            raise BuildActionError("liftControl is not set")
        if not self.toePivot:
            raise BuildActionError("toePivot is not set")
        if not self.ballPivot:
            raise BuildActionError("ballPivot is not set")
        if not self.heelPivot:
            raise BuildActionError("heelPivot is not set")

    def run(self):
        shouldCreateOffset = False
        if self.createFollowerOffset == 0:
            # Always
            shouldCreateOffset = True
        elif self.createFollowerOffset == 1 and self.follower.nodeType() != 'joint':
            # Exclude Joints and the follower is not a joint
            shouldCreateOffset = True

        _follower = self.follower
        _toeFollower = self.toeFollower
        if shouldCreateOffset:
            _follower = pulse.nodes.createOffsetTransform(self.follower)
            _toeFollower = pulse.nodes.createOffsetTransform(self.toeFollower)

        # TODO(bsayre): expose as option
        self.useCustomAttrs = False

        if self.useCustomAttrs:
            # create 'lift' and 'ballToe' blend attrs
            self.control.addAttr(
                "ballToe", min=0, max=1, at='double', defaultValue=0, keyable=1)
            ballToeAttr = self.control.attr('ballToe')
            self.control.addAttr(
                "lift", min=0, max=1, at='double', defaultValue=0, keyable=1)
            liftAttr = self.control.attr('lift')

            lockedAttrs = ['tx', 'ty', 'tz', 'sx', 'sy', 'sz']
        else:
            # use tx and tz to control ball toe and lift blend
            ballToeAttr = self.control.tx
            liftAttr = self.control.tz
            # configure magic control
            # limit translate attrs and use them to drive blends
            pm.transformLimits(self.control, tx=(0, 1), tz=(0, 1),
                               etz=(True, True), etx=(True, True))
            lockedAttrs = ['ty', 'sx', 'sy', 'sz']

        # lockup attributes on the magic control
        for attrName in lockedAttrs:
            attr = self.control.attr(attrName)
            attr.setKeyable(False)
            attr.showInChannelBox(False)
            attr.setLocked(True)

        # transform that will contain the final results of planted targets
        if self.plantedTarget:
            planted_tgt = self.plantedTarget
        else:
            planted_tgt = pm.group(
                em=True, p=self.control,
                n='{0}_mf_anklePlanted_tgt'.format(self.follower.nodeName()))
        # use liftControl directly as target
        lifted_tgt = self.liftControl

        # toe tgt is only used for the toe follower, not the main ankle follower
        # (keeps toe control fully locked when using ball pivot)
        toeDown_tgt = pm.group(
            em=True, p=self.toePivot,
            n='{0}_mf_toeDown_tgt'.format(self.toeFollower.nodeName()))
        toeUp_tgt = pm.group(
            em=True, p=_toeFollower.getParent(),
            n='{0}_mf_toeUp_tgt'.format(self.toeFollower.nodeName()))
        # ball pivot will contain result of both toe and ball pivot
        ballToe_tgt = pm.group(
            em=True, p=self.ballPivot,
            n='{0}_mf_ballToe_tgt'.format(self.follower.nodeName()))
        heel_tgt = pm.group(
            em=True, p=self.heelPivot,
            n='{0}_mf_heel_tgt'.format(self.follower.nodeName()))

        followerMtx = pulse.nodes.getWorldMatrix(self.follower)
        toeFollowerMtx = pulse.nodes.getWorldMatrix(self.toeFollower)

        # update pivots to match world rotation of control and create
        # offset so that direct connect rotations will match up
        for node in (self.toePivot, self.ballPivot, self.heelPivot):
            followerMtx.translate = (0, 0, 0)
            followerMtx.scale = (1, 1, 1)
            pulse.nodes.setWorldMatrix(node, followerMtx)
            pulse.nodes.createOffsetTransform(node)
            if node == self.toePivot:
                # after orienting toe pivot, re-parent ballPivot
                self.ballPivot.setParent(self.toePivot)

        # update toe target transforms to match toe follower transform
        for node in (toeDown_tgt, toeUp_tgt):
            pulse.nodes.setWorldMatrix(node, toeFollowerMtx)

        # update target transforms to match follower transform
        # (basically preserves offsets on the follower)
        for node in (ballToe_tgt, heel_tgt):  # , ankle_tgt):
            pulse.nodes.setWorldMatrix(node, followerMtx)

        # connect direct rotations to heel pivot done after creating targets so that
        # the targets WILL move to reflect magic control non-zero rotations (if any)
        self.control.r >> self.heelPivot.r

        # connect blended rotation to toe / ball pivots
        # use ballToe attr to drive the blend (0 == ball, 1 == toe)
        toeRotBlendAttr = pulse.utilnodes.blend2(
            self.control.r, (0, 0, 0), ballToeAttr)
        ballRotBlendAttr = pulse.utilnodes.blend2(
            (0, 0, 0), self.control.r, ballToeAttr)
        toeRotBlendAttr >> self.toePivot.r
        ballRotBlendAttr >> self.ballPivot.r

        # hide and lock the now-connected pivots
        for node in (self.toePivot, self.ballPivot, self.heelPivot):
            node.t.lock()
            node.r.lock()
            node.s.lock()
            node.v.set(False)

        # create condition to switch between ball/toe and heel pivots
        # TODO(bsayre): use dot-product towards up to determine toe vs heel
        isToeRollAttr = pulse.utilnodes.condition(self.control.ry, 0, [1], [0], 2)
        plantedMtxAttr = pulse.utilnodes.choice(
            isToeRollAttr, heel_tgt.wm, ballToe_tgt.wm)

        # connect final planted ankle matrix to ankle target transform
        pulse.nodes.connectMatrix(plantedMtxAttr, planted_tgt, pulse.nodes.ConnectMatrixMethod.SNAP)
        planted_tgt.t.lock()
        planted_tgt.r.lock()
        planted_tgt.s.lock()
        planted_tgt.v.setKeyable(False)
        # create matrix blend between planted and lifted targets
        # use lift attr to drive the blend (0 == planted, 1 == lifted)
        plantedLiftedBlendAttr = self.createMatrixBlend(
            planted_tgt.wm, lifted_tgt.wm, liftAttr,
            '{0}_mf_plantedLiftedBlend'.format(self.follower.nodeName()))

        # connect final matrix to follower
        # TODO(bsayre): this connect eliminates all transform inheritance, is
        #   world space control what we want? or do we need to inject offsets and
        #   allow parent transforms to come through
        pulse.nodes.connectMatrix(plantedLiftedBlendAttr, _follower, pulse.nodes.ConnectMatrixMethod.SNAP)

        # create toe up/down matrix blend, (0 == toe-up, 1 == toe-down/ball pivot)
        # in order to do this, reverse ballToe attr, then multiply by isToeRoll
        # to ensure toe-down is not active when not using toe pivots
        # reverse ballToeAttr, so that 1 == toe-down/ball
        ballToeReverseAttr = pulse.utilnodes.reverse(ballToeAttr)
        # multiply by isToe to ensure ball not active while using heel pivot
        isToeAndBallAttr = pulse.utilnodes.multiply(
            ballToeReverseAttr, isToeRollAttr)
        # multiply by 1-liftAttr to ensure ball not active while lifting
        liftReverseAttr = pulse.utilnodes.reverse(liftAttr)
        toeUpDownBlendAttr = pulse.utilnodes.multiply(isToeAndBallAttr, liftReverseAttr)
        ballToeMtxBlendAttr = self.createMatrixBlend(
            toeUp_tgt.wm, toeDown_tgt.wm, toeUpDownBlendAttr,
            '{0}_mf_toeUpDownBlend'.format(self.toeFollower.nodeName()))

        # connect final toe rotations to toeFollower
        # TODO(bsayre): parent both tgts to ankle somehow to prevent locking
        pulse.nodes.connectMatrix(ballToeMtxBlendAttr, _toeFollower, pulse.nodes.ConnectMatrixMethod.SNAP)

        # add meta data to controls
        ctlData = {
            'plantedTarget': planted_tgt,
            'liftControl': self.liftControl,
        }
        meta.setMetaData(
            self.control, MAGIC_FEET_CTL_METACLASSNAME, ctlData, False)

        liftCtlData = {
            'control': self.control
        }
        meta.setMetaData(
            self.liftControl, MAGIC_FEET_LIFT_CTL_METACLASSNAME, liftCtlData, False)

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
        pulse.utilnodes.reverse(blendAttr) >> blendNode.wtMatrix[0].weightIn

        mtxB >> blendNode.wtMatrix[1].matrixIn
        blendAttr >> blendNode.wtMatrix[1].weightIn

        return blendNode.matrixSum
