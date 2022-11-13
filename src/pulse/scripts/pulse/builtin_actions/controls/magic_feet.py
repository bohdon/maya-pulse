import pymel.core as pm

from pulse import nodes, util_nodes
from pulse.vendor import pymetanode as meta
from pulse.build_items import BuildAction, BuildActionError
from pulse.build_items import BuildActionAttributeType as AttrType

MAGIC_FEET_CTL_METACLASSNAME = 'pulse_magicfeet_ctl'
MAGIC_FEET_LIFT_CTL_METACLASSNAME = 'pulse_magicfeet_lift_ctl'


class MagicFeetAction(BuildAction):
    """
    Allows controlling foot rotation, blending pivots between toe, heel and ankle.
    """

    id = 'Pulse.MagicFeet'
    display_name = 'Magic Feet'
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
        should_create_offset = False
        if self.createFollowerOffset == 0:
            # Always
            should_create_offset = True
        elif self.createFollowerOffset == 1 and self.follower.nodeType() != 'joint':
            # Exclude Joints and the follower is not a joint
            should_create_offset = True

        _follower = self.follower
        _toeFollower = self.toeFollower
        if should_create_offset:
            _follower = nodes.create_offset_transform(self.follower)
            _toeFollower = nodes.create_offset_transform(self.toeFollower)

        # TODO(bsayre): expose as option
        use_custom_attrs = False

        if use_custom_attrs:
            # create 'lift' and 'ballToe' blend attrs
            self.control.addAttr(
                "ballToe", min=0, max=1, at='double', defaultValue=0, keyable=1)
            ball_toe_attr = self.control.attr('ballToe')
            self.control.addAttr(
                "lift", min=0, max=1, at='double', defaultValue=0, keyable=1)
            lift_attr = self.control.attr('lift')

            locked_attrs = ['tx', 'ty', 'tz', 'sx', 'sy', 'sz']
        else:
            # use tx and tz to control ball toe and lift blend
            ball_toe_attr = self.control.tx
            lift_attr = self.control.tz
            # configure magic control
            # limit translate attrs and use them to drive blends
            pm.transformLimits(self.control, tx=(0, 1), tz=(0, 1), etz=(True, True), etx=(True, True))
            locked_attrs = ['ty', 'sx', 'sy', 'sz']

        # lockup attributes on the magic control
        for attrName in locked_attrs:
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
        toe_down_tgt = pm.group(
            em=True, p=self.toePivot,
            n='{0}_mf_toeDown_tgt'.format(self.toeFollower.nodeName()))
        toe_up_tgt = pm.group(
            em=True, p=_toeFollower.getParent(),
            n='{0}_mf_toeUp_tgt'.format(self.toeFollower.nodeName()))
        # ball pivot will contain result of both toe and ball pivot
        ball_toe_tgt = pm.group(
            em=True, p=self.ballPivot,
            n='{0}_mf_ballToe_tgt'.format(self.follower.nodeName()))
        heel_tgt = pm.group(
            em=True, p=self.heelPivot,
            n='{0}_mf_heel_tgt'.format(self.follower.nodeName()))

        follower_mtx = nodes.get_world_matrix(self.follower)
        toe_follower_mtx = nodes.get_world_matrix(self.toeFollower)

        # update pivots to match world rotation of control and create
        # offset so that direct connect rotations will match up
        for node in (self.toePivot, self.ballPivot, self.heelPivot):
            follower_mtx.translate = (0, 0, 0)
            follower_mtx.scale = (1, 1, 1)
            nodes.set_world_matrix(node, follower_mtx)
            nodes.create_offset_transform(node)
            if node == self.toePivot:
                # after orienting toe pivot, re-parent ballPivot
                self.ballPivot.setParent(self.toePivot)

        # update toe target transforms to match toe follower transform
        for node in (toe_down_tgt, toe_up_tgt):
            nodes.set_world_matrix(node, toe_follower_mtx)

        # update target transforms to match follower transform
        # (basically preserves offsets on the follower)
        for node in (ball_toe_tgt, heel_tgt):  # , ankle_tgt):
            nodes.set_world_matrix(node, follower_mtx)

        # connect direct rotations to heel pivot done after creating targets so that
        # the targets WILL move to reflect magic control non-zero rotations (if any)
        self.control.r >> self.heelPivot.r

        # connect blended rotation to toe / ball pivots
        # use ballToe attr to drive the blend (0 == ball, 1 == toe)
        toe_rot_blend_attr = util_nodes.blend2(self.control.r, (0, 0, 0), ball_toe_attr)
        ball_rot_blend_attr = util_nodes.blend2((0, 0, 0), self.control.r, ball_toe_attr)
        toe_rot_blend_attr >> self.toePivot.r
        ball_rot_blend_attr >> self.ballPivot.r

        # hide and lock the now-connected pivots
        for node in (self.toePivot, self.ballPivot, self.heelPivot):
            node.t.lock()
            node.r.lock()
            node.s.lock()
            node.v.set(False)

        # create condition to switch between ball/toe and heel pivots
        # TODO(bsayre): use dot-product towards up to determine toe vs heel
        is_toe_roll_attr = util_nodes.condition(self.control.ry, 0, [1], [0], 2)
        planted_mtx_attr = util_nodes.choice(is_toe_roll_attr, heel_tgt.wm, ball_toe_tgt.wm)

        # connect final planted ankle matrix to ankle target transform
        nodes.connect_matrix(planted_mtx_attr, planted_tgt, nodes.ConnectMatrixMethod.SNAP)
        planted_tgt.t.lock()
        planted_tgt.r.lock()
        planted_tgt.s.lock()
        planted_tgt.v.setKeyable(False)
        # create matrix blend between planted and lifted targets
        # use lift attr to drive the blend (0 == planted, 1 == lifted)
        planted_lifted_blend_attr = self.create_matrix_blend(
            planted_tgt.wm, lifted_tgt.wm, lift_attr,
            '{0}_mf_plantedLiftedBlend'.format(self.follower.nodeName()))

        # connect final matrix to follower
        # TODO(bsayre): this connect eliminates all transform inheritance, is
        #   world space control what we want? or do we need to inject offsets and
        #   allow parent transforms to come through
        nodes.connect_matrix(planted_lifted_blend_attr, _follower, nodes.ConnectMatrixMethod.SNAP)

        # create toe up/down matrix blend, (0 == toe-up, 1 == toe-down/ball pivot)
        # in order to do this, reverse ballToe attr, then multiply by isToeRoll
        # to ensure toe-down is not active when not using toe pivots
        # reverse ballToeAttr, so that 1 == toe-down/ball
        ball_toe_reverse_attr = util_nodes.reverse(ball_toe_attr)
        # multiply by isToe to ensure ball not active while using heel pivot
        is_toe_and_ball_attr = util_nodes.multiply(
            ball_toe_reverse_attr, is_toe_roll_attr)
        # multiply by 1-liftAttr to ensure ball not active while lifting
        lift_reverse_attr = util_nodes.reverse(lift_attr)
        toe_up_down_blend_attr = util_nodes.multiply(is_toe_and_ball_attr, lift_reverse_attr)
        ball_toe_mtx_blend_attr = self.create_matrix_blend(
            toe_up_tgt.wm, toe_down_tgt.wm, toe_up_down_blend_attr,
            '{0}_mf_toeUpDownBlend'.format(self.toeFollower.nodeName()))

        # connect final toe rotations to toeFollower
        # TODO(bsayre): parent both tgts to ankle somehow to prevent locking
        nodes.connect_matrix(ball_toe_mtx_blend_attr, _toeFollower, nodes.ConnectMatrixMethod.SNAP)

        # add meta data to controls
        ctl_data = {
            'plantedTarget': planted_tgt,
            'liftControl': self.liftControl,
        }
        meta.set_metadata(
            self.control, MAGIC_FEET_CTL_METACLASSNAME, ctl_data, False)

        lift_ctl_data = {
            'control': self.control
        }
        meta.set_metadata(
            self.liftControl, MAGIC_FEET_LIFT_CTL_METACLASSNAME, lift_ctl_data, False)

    def create_matrix_blend(self, mtx_a, mtx_b, blend_attr, name):
        """
        Create a util node to blend between two matrices.

        Args:
            mtx_a (Attribute): Matrix attribute to use when blend_attr is 0
            mtx_b (Attribute): Matrix attribute to use when blend_attr is 1
            blend_attr (Attribute): Float attribute to blend between the matrices
            name (str): The name of the new node

        Returns:
            The blended output attr of the node that was created
        """
        blend_node = pm.createNode('wtAddMatrix', n=name)

        mtx_a >> blend_node.wtMatrix[0].matrixIn
        util_nodes.reverse(blend_attr) >> blend_node.wtMatrix[0].weightIn

        mtx_b >> blend_node.wtMatrix[1].matrixIn
        blend_attr >> blend_node.wtMatrix[1].weightIn

        return blend_node.matrixSum
