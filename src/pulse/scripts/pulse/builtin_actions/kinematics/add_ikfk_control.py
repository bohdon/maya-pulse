import pymel.core as pm

from pulse import nodes, util_nodes
from pulse.build_items import BuildAction, BuildActionError
from pulse.build_items import BuildActionAttributeType as AttrType


class AddIKFKControlAction(BuildAction):
    id = 'Pulse.AddIKFKControl'
    display_name = 'Add IKFK Control'
    description = 'Adds a control to an existing IKFK switch, allowing it to have different parent spaces for IK and FK'
    color = (.4, .6, .8)
    category = 'Kinematics'

    attr_definitions = [
        dict(name='ikfkControl', type=AttrType.NODE, description="The control with the IKFK switch attribute"),
        dict(name='follower', type=AttrType.NODE, description="The node that will switch between parent spaces"),
        dict(name='ikLeader', type=AttrType.NODE, description="The leader node to use while in IK mode"),
        dict(name='fkLeader', type=AttrType.NODE, description="The leader node to use while in FK mode"),
        dict(name='preservePosition', type=AttrType.BOOL, value=True,
             description="If true, preserve the followers world space position when the connections are made"),
    ]

    def validate(self):
        if not self.ikfkControl:
            raise BuildActionError('ikfkControl must be set')
        if not self.follower:
            raise BuildActionError('follower must be set')
        if not self.ikLeader:
            raise BuildActionError('ikLeader must be set')
        if not self.fkLeader:
            raise BuildActionError('fkLeader must be set')

    def run(self):
        ik_attr = self.ikfkControl.attr('ik')
        if not ik_attr:
            raise BuildActionError(f"ikfkControl has no IK attribute: {self.ikfkControl}")

        if self.preservePosition:
            follower_pm = self.follower.pm.get()
            fk_offset = follower_pm * self.fkLeader.wim.get()
            ik_offset = follower_pm * self.ikLeader.wim.get()
            fk_mtx = util_nodes.mult_matrix(pm.dt.Matrix(fk_offset), self.fkLeader.wm)
            fk_mtx.node().rename(f"{self.follower.nodeName()}_ikfk_fk_offset")
            ik_mtx = util_nodes.mult_matrix(pm.dt.Matrix(ik_offset), self.ikLeader.wm)
            ik_mtx.node().rename(f"{self.follower.nodeName()}_ikfk_ik_offset")
            mtx_choice = util_nodes.choice(ik_attr, fk_mtx, ik_mtx)
        else:
            mtx_choice = util_nodes.choice(ik_attr, self.fkLeader.wm, self.ikLeader.wm)

        mtx_choice.node().rename(f"{self.follower.nodeName()}_ikfk_choice")

        # don't preserve position here, because offsets have already been calculated above
        nodes.connect_matrix(mtx_choice, self.follower, nodes.ConnectMatrixMethod.SNAP)
