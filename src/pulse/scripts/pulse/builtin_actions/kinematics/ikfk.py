import pymel.core as pm

from pulse import nodes, util_nodes, joints, control_shapes
from pulse.vendor import pymetanode as meta
from pulse.core import BuildAction, BuildActionError
from pulse.core import BuildActionAttributeType as AttrType
from pulse.ui.contextmenus import PulseNodeContextSubMenu

IKFK_CONTROL_METACLASS = "pulse_ikfk_control"


class ThreeBoneIKFKAction(BuildAction):
    """
    Create a 3-bone IK chain that can switch to FK.
    """

    id = "Pulse.ThreeBoneIKFK"
    display_name = "3-Bone IK FK"
    color = (0.4, 0.6, 0.8)
    category = "Kinematics"

    attr_definitions = [
        dict(
            name="endJoint",
            type=AttrType.NODE,
            description="The end joint of the IK chain. Mid and root joint are retrieved automatically",
        ),
        dict(
            name="rootCtl",
            type=AttrType.NODE,
            description="The root joint control",
        ),
        dict(
            name="midCtlIk",
            type=AttrType.NODE,
            description="The mid joint control during IK (the pole vector control)",
        ),
        dict(
            name="midCtlFk",
            type=AttrType.NODE,
            description="The mid joint control during FK",
        ),
        dict(
            name="endCtlIk",
            type=AttrType.NODE,
            description="The end joint control during IK",
        ),
        dict(
            name="endCtlFk",
            type=AttrType.NODE,
            description="The end joint control during FK",
        ),
        dict(
            name="addPoleLine",
            type=AttrType.BOOL,
            value=True,
            description="Add a curve shape to the mid FK control that draws a line to the bone",
        ),
        dict(
            name="extraControls",
            type=AttrType.NODE_LIST,
            optional=True,
            description="Additional controls to add ikfk metadata to, so they can be used with ikfk switching utils",
        ),
    ]

    def run(self):
        # retrieve mid and root joints
        mid_joint = self.endJoint.getParent()
        root_joint = mid_joint.getParent()

        # duplicate joints for ik chain
        ik_joint_name_fmt = "{0}_ik"
        ik_jnts = nodes.duplicate_branch(root_joint, self.endJoint, name_fmt=ik_joint_name_fmt)

        for j in ik_jnts:
            # TODO: debug settings for build actions
            j.v.set(True)

        root_ik_joint = ik_jnts[0]
        mid_ik_joint = ik_jnts[1]
        end_ik_joint = ik_jnts[2]

        # parent ik joints to root control
        root_ik_joint.setParent(self.rootCtl)

        # create ik and hook up pole object and controls
        handle, effector = pm.ikHandle(
            name=f"{end_ik_joint}_ikHandle",
            startJoint=root_ik_joint,
            endEffector=end_ik_joint,
            solver="ikRPsolver",
        )

        # add twist attr to end control
        self.endCtlIk.addAttr("twist", at="double", k=1)
        self.endCtlIk.twist >> handle.twist

        # connect mid ik ctl (pole vector)
        pm.poleVectorConstraint(self.midCtlIk, handle)

        # parent ik handle to end control
        handle.setParent(self.endCtlIk)

        # TODO: use pick matrix and mult matrix to combine location from ik system with rotation/scale of ctl
        # constraint end joint scale and rotation to end control
        pm.orientConstraint(self.endCtlIk, end_ik_joint, maintainOffset=True)
        pm.scaleConstraint(self.endCtlIk, end_ik_joint, maintainOffset=True)

        # setup ikfk switch attr (integer, not blend)
        self.rootCtl.addAttr("ik", min=0, max=1, attributeType="short", defaultValue=1, keyable=1)
        ik_attr = self.rootCtl.attr("ik")

        # create choices for world matrix from ik and fk targets
        root_choice = util_nodes.choice(ik_attr, self.rootCtl.wm, root_ik_joint.wm)
        root_choice.node().rename(f"{root_joint.nodeName()}_ikfk_choice")
        mid_choice = util_nodes.choice(ik_attr, self.midCtlFk.wm, mid_ik_joint.wm)
        mid_choice.node().rename(f"{mid_joint.nodeName()}_ikfk_choice")
        end_choice = util_nodes.choice(ik_attr, self.endCtlFk.wm, end_ik_joint.wm)
        end_choice.node().rename(f"{self.endJoint.nodeName()}_ikfk_choice")

        # connect the target matrices to the joints
        nodes.connect_matrix(root_choice, root_joint, nodes.ConnectMatrixMethod.SNAP)
        nodes.connect_matrix(mid_choice, mid_joint, nodes.ConnectMatrixMethod.SNAP)
        nodes.connect_matrix(end_choice, self.endJoint, nodes.ConnectMatrixMethod.SNAP)

        # connect visibility
        self.midCtlIk.v.setLocked(False)
        self.endCtlIk.v.setLocked(False)
        ik_attr >> self.midCtlIk.v
        ik_attr >> self.endCtlIk.v

        fk_attr = util_nodes.reverse(ik_attr)
        self.midCtlFk.v.setLocked(False)
        self.endCtlFk.v.setLocked(False)
        fk_attr >> self.midCtlFk.v
        fk_attr >> self.endCtlFk.v

        # add connecting line shape
        if self.addPoleLine:
            # keep consistent color overrides for the mid ctl
            color = nodes.get_override_color(self.midCtlIk)
            control_shapes.create_line_shape(mid_ik_joint, self.midCtlIk, self.midCtlIk)
            if color:
                nodes.set_override_color(self.midCtlIk, color)

        # cleanup
        handle.v.set(False)
        for jnt in ik_jnts:
            # TODO: lock attrs
            jnt.v.set(False)

        # add metadata to controls
        ikfk_ctl_data = {
            "root_fk_ctl": self.rootCtl,
            "mid_fk_ctl": self.midCtlFk,
            "end_fk_ctl": self.endCtlFk,
            "root_ik_ctl": self.rootCtl,
            "mid_ik_ctl": self.midCtlIk,
            "end_ik_ctl": self.endCtlIk,
            "end_joint": self.endJoint,
        }

        ikfk_ctls = {self.rootCtl, self.midCtlIk, self.endCtlIk, self.midCtlFk, self.endCtlFk}
        if self.extraControls:
            ikfk_ctls.update(self.extraControls)
        for ctl in ikfk_ctls:
            meta.set_metadata(ctl, IKFK_CONTROL_METACLASS, ikfk_ctl_data)


class IKFKControlUtils(object):
    """
    Utils for working with IKFK controls
    """

    @staticmethod
    def get_ikfk_data(ctl):
        return meta.get_metadata(ctl, IKFK_CONTROL_METACLASS)

    @staticmethod
    def get_ikfk_joint_matrices(ikfk_data: dict):
        """
        Return the list of matrices for the IKFK joint chain in the order (root, middle, end)
        """
        end_joint = ikfk_data.get("end_joint")
        if not end_joint:
            pm.warning(f"IKFK data is missing end_joint: {ikfk_data}")
            return None, None, None

        mid_joint = end_joint.getParent()
        root_joint = mid_joint.getParent()

        return root_joint.wm.get(), mid_joint.wm.get(), end_joint.wm.get()

    @staticmethod
    def switch_to_fk(ctl):
        ikfk_data = IKFKControlUtils.get_ikfk_data(ctl)

        # get joint matrices
        root_mtx, mid_mtx, end_mtx = IKFKControlUtils.get_ikfk_joint_matrices(ikfk_data)
        if root_mtx is None:
            return

        # get fk controls
        root_fk_ctl = ikfk_data.get("root_fk_ctl")
        mid_fk_ctl = ikfk_data.get("mid_fk_ctl")
        end_fk_ctl = ikfk_data.get("end_fk_ctl")
        if not root_fk_ctl or not mid_fk_ctl or not end_fk_ctl:
            pm.warning(f"IKFK data has missing fk ctls: {ctl}")
            return

        if root_fk_ctl.attr("ik").get() == 0:
            # already in FK
            return

        # TODO: add support for joint-to-ctl offsets
        # snap to joints pretty much exactly
        nodes.set_world_matrix(root_fk_ctl, root_mtx)
        nodes.set_world_matrix(mid_fk_ctl, mid_mtx)
        nodes.set_world_matrix(end_fk_ctl, end_mtx)

        root_fk_ctl.attr("ik").set(0)

    @staticmethod
    def switch_to_ik(ctl):
        ikfk_data = IKFKControlUtils.get_ikfk_data(ctl)

        # get joint matrices
        root_mtx, mid_mtx, end_mtx = IKFKControlUtils.get_ikfk_joint_matrices(ikfk_data)
        if root_mtx is None:
            return

        # get ik controls
        root_ik_ctl = ikfk_data.get("root_ik_ctl")
        mid_ik_ctl = ikfk_data.get("mid_ik_ctl")
        end_ik_ctl = ikfk_data.get("end_ik_ctl")
        if not root_ik_ctl or not mid_ik_ctl or not end_ik_ctl:
            pm.warning(f"IKFK data has missing ik ctls: {ctl}")
            return

        if root_ik_ctl.attr("ik").get() == 1:
            # already in IK
            return

        # TODO: add support for joint-to-ctl offsets
        # TODO: incorporate delegate ctls into all 'move anim ctl here' functionality
        # move foot, and calculate new pole vector
        end_ik_move_ctl = IKFKControlUtils.get_delegate_control(end_ik_ctl)
        nodes.set_world_matrix(end_ik_move_ctl, end_mtx)

        # move ik pole ctl
        new_pole_pos = IKFKControlUtils.calculate_ik_pole_ctl_location(
            mid_ik_ctl, root_mtx.translate, mid_mtx.translate, end_mtx.translate
        )
        mid_ik_ctl.setTranslation(new_pole_pos, space="world")

        root_ik_ctl.attr("ik").set(1)

    @staticmethod
    def get_delegate_control(node):
        ctl_delegate_data = meta.get_metadata(node, "pulse_ctl_delegate")
        if ctl_delegate_data:
            return ctl_delegate_data["delegate_ctl"]
        return node

    @staticmethod
    def calculate_ik_pole_ctl_location(ctl, root: pm.dt.Vector, mid: pm.dt.Vector, end: pm.dt.Vector):
        """
        Calculate the new position for an ik pole ctl given the matrices of the ikfk joints
        """
        # TODO: use IKPoleLinkPositioner functionality already in pulse

        pole_vector, pole_mid = joints.get_ik_pole_vector_and_mid_point(root, mid, end)

        # calculate distance based on followers current location
        current_dist = pole_vector.dot(ctl.getTranslation(space="world") - pole_mid)

        # keep pole vector in front, by at least 2x the distance from root to mid-joint
        min_dist = 2 * (pm.dt.Vector(root) - pm.dt.Vector(mid)).length()
        dist = max(current_dist, min_dist)

        # calculate new pole position at the new distance
        return pole_mid + pole_vector * dist


class IKFKControlContextSubmenu(PulseNodeContextSubMenu):
    """
    Provides IKFK switching options on related controls.
    """

    @classmethod
    def should_build_sub_menu(cls, menu) -> bool:
        return cls.is_node_with_metaclass_selected(IKFK_CONTROL_METACLASS)

    def build_menu_items(self):
        pm.menuItem(
            label="Switch To FK",
            radialPosition=self.get_safe_radial_position("NW"),
            command=pm.Callback(self.switch_to_fk_for_selected),
        )
        pm.menuItem(
            label="Switch To IK",
            radialPosition=self.get_safe_radial_position("SW"),
            command=pm.Callback(self.switch_to_ik_for_selected),
        )

    def switch_to_ik_for_selected(self):
        sel_ctls = self.get_selected_nodes_with_meta_class(IKFK_CONTROL_METACLASS)
        for ctl in sel_ctls:
            IKFKControlUtils.switch_to_ik(ctl)

    def switch_to_fk_for_selected(self):
        sel_ctls = self.get_selected_nodes_with_meta_class(IKFK_CONTROL_METACLASS)
        for ctl in sel_ctls:
            IKFKControlUtils.switch_to_fk(ctl)
