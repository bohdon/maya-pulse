import pymel.core as pm

import pulse.controlshapes
import pulse.joints
import pulse.nodes
import pulse.utilnodes
import pymetanode as meta
from pulse.buildItems import BuildAction, BuildActionError
from pulse.ui.contextmenus import PulseNodeContextSubMenu

IKFK_CONTROL_METACLASS = 'pulse_ikfk_control'


class ThreeBoneIKFKAction(BuildAction):

    def validate(self):
        if not self.endJoint:
            raise BuildActionError('endJoint must be set')
        if not self.rootCtl:
            raise BuildActionError('rootCtl must be set')
        if not self.midCtlIk:
            raise BuildActionError('midCtlIk must be set')
        if not self.midCtlFk:
            raise BuildActionError('midCtlFk must be set')
        if not self.endCtlIk:
            raise BuildActionError('endCtlIk must be set')
        if not self.endCtlFk:
            raise BuildActionError('endCtlFk must be set')

    def run(self):
        # retrieve mid and root joints
        midJoint = self.endJoint.getParent()
        rootJoint = midJoint.getParent()

        # duplicate joints for ik chain
        ikJointNameFmt = '{0}_ik'
        ikjnts = pulse.nodes.duplicateBranch(
            rootJoint, self.endJoint, nameFmt=ikJointNameFmt)
        for j in ikjnts:
            # TODO: debug settings for build actions
            j.v.set(True)
        rootIkJoint = ikjnts[0]
        midIkJoint = ikjnts[1]
        endIkJoint = ikjnts[2]

        # parent ik joints to root control
        rootIkJoint.setParent(self.rootCtl)

        # create ik and hook up pole object and controls
        handle, effector = pm.ikHandle(
            name="{0}_ikHandle".format(endIkJoint),
            startJoint=rootIkJoint,
            endEffector=endIkJoint,
            solver="ikRPsolver")

        # add twist attr to end control
        self.endCtlIk.addAttr('twist', at='double', k=1)
        self.endCtlIk.twist >> handle.twist

        # connect mid ik ctl (pole vector)
        pm.poleVectorConstraint(self.midCtlIk, handle)

        # parent ik handle to end control
        handle.setParent(self.endCtlIk)

        # TODO: use pick matrix and mult matrix to combine location from ik system with rotation/scale of ctl
        # constraint end joint scale and rotation to end control
        pm.orientConstraint(self.endCtlIk, endIkJoint, mo=True)
        pm.scaleConstraint(self.endCtlIk, endIkJoint, mo=True)

        # setup ikfk switch attr (integer, not blend)
        self.rootCtl.addAttr("ik", min=0, max=1, at='short',
                             defaultValue=1, keyable=1)
        ikAttr = self.rootCtl.attr("ik")

        # create choices for world matrix from ik and fk targets
        rootChoice = pulse.utilnodes.choice(
            ikAttr, self.rootCtl.wm, rootIkJoint.wm)
        rootChoice.node().rename(f"{rootJoint.nodeName()}_ikfk_choice")
        midChoice = pulse.utilnodes.choice(
            ikAttr, self.midCtlFk.wm, midIkJoint.wm)
        midChoice.node().rename(f"{midJoint.nodeName()}_ikfk_choice")
        endChoice = pulse.utilnodes.choice(
            ikAttr, self.endCtlFk.wm, endIkJoint.wm)
        endChoice.node().rename(f"{self.endJoint.nodeName()}_ikfk_choice")

        # connect the target matrices to the joints
        pulse.nodes.connectMatrix(rootChoice, rootJoint, pulse.nodes.ConnectMatrixMethod.SNAP)
        pulse.nodes.connectMatrix(midChoice, midJoint, pulse.nodes.ConnectMatrixMethod.SNAP)
        pulse.nodes.connectMatrix(endChoice, self.endJoint, pulse.nodes.ConnectMatrixMethod.SNAP)

        # connect visibility
        self.midCtlIk.v.setLocked(False)
        self.endCtlIk.v.setLocked(False)
        ikAttr >> self.midCtlIk.v
        ikAttr >> self.endCtlIk.v

        fkAttr = pulse.utilnodes.reverse(ikAttr)
        self.midCtlFk.v.setLocked(False)
        self.endCtlFk.v.setLocked(False)
        fkAttr >> self.midCtlFk.v
        fkAttr >> self.endCtlFk.v

        # add connecting line shape
        if self.addPoleLine:
            # keep consistent color overrides for the mid ctl
            color = pulse.nodes.getOverrideColor(self.midCtlIk)
            pulse.controlshapes.createLineShape(
                midIkJoint, self.midCtlIk, self.midCtlIk)
            if color:
                pulse.nodes.setOverrideColor(self.midCtlIk, color)

        # cleanup
        handle.v.set(False)
        for jnt in ikjnts:
            # TODO: lock attrs
            jnt.v.set(False)

        # add metadata to controls
        ikfk_ctl_data = {
            'root_fk_ctl': self.rootCtl,
            'mid_fk_ctl': self.midCtlFk,
            'end_fk_ctl': self.endCtlFk,
            'root_ik_ctl': self.rootCtl,
            'mid_ik_ctl': self.midCtlIk,
            'end_ik_ctl': self.endCtlIk,
            'end_joint': self.endJoint,
        }

        ikfk_ctls = {self.rootCtl, self.midCtlIk, self.endCtlIk, self.midCtlFk, self.endCtlFk}
        if self.extraControls:
            ikfk_ctls.update(self.extraControls)
        for ctl in ikfk_ctls:
            meta.setMetaData(ctl, IKFK_CONTROL_METACLASS, ikfk_ctl_data)


class IKFKControlUtils(object):
    """
    Utils for working with IKFK controls
    """

    @staticmethod
    def getIKFKData(ctl):
        return meta.getMetaData(ctl, IKFK_CONTROL_METACLASS)

    @staticmethod
    def getIKFKJointMatrices(ikfk_data: dict):
        """
        Return the list of matrices for the IKFK joint chain in the order (root, middle, end)
        """
        end_joint = ikfk_data.get('end_joint')
        if not end_joint:
            pm.warning(f"IKFK data is missing end_joint: {ikfk_data}")
            return None, None, None

        mid_joint = end_joint.getParent()
        root_joint = mid_joint.getParent()

        return root_joint.wm.get(), mid_joint.wm.get(), end_joint.wm.get()

    @staticmethod
    def switchToFK(ctl):
        ikfk_data = IKFKControlUtils.getIKFKData(ctl)

        # get joint matrices
        root_mtx, mid_mtx, end_mtx = IKFKControlUtils.getIKFKJointMatrices(ikfk_data)
        if root_mtx is None:
            return

        # get fk controls
        root_fk_ctl = ikfk_data.get('root_fk_ctl')
        mid_fk_ctl = ikfk_data.get('mid_fk_ctl')
        end_fk_ctl = ikfk_data.get('end_fk_ctl')
        if not root_fk_ctl or not mid_fk_ctl or not end_fk_ctl:
            pm.warning(f"IKFK data has missing fk ctls: {ctl}")
            return

        if root_fk_ctl.attr('ik').get() == 0:
            # already in FK
            return

        # TODO: add support for joint-to-ctl offsets
        # snap to joints pretty much exactly
        pulse.nodes.setWorldMatrix(root_fk_ctl, root_mtx)
        pulse.nodes.setWorldMatrix(mid_fk_ctl, mid_mtx)
        pulse.nodes.setWorldMatrix(end_fk_ctl, end_mtx)

        root_fk_ctl.attr('ik').set(0)

    @staticmethod
    def switchToIK(ctl):
        ikfk_data = IKFKControlUtils.getIKFKData(ctl)

        # get joint matrices
        root_mtx, mid_mtx, end_mtx = IKFKControlUtils.getIKFKJointMatrices(ikfk_data)
        if root_mtx is None:
            return

        # get ik controls
        root_ik_ctl = ikfk_data.get('root_ik_ctl')
        mid_ik_ctl = ikfk_data.get('mid_ik_ctl')
        end_ik_ctl = ikfk_data.get('end_ik_ctl')
        if not root_ik_ctl or not mid_ik_ctl or not end_ik_ctl:
            pm.warning(f"IKFK data has missing ik ctls: {ctl}")
            return

        if root_ik_ctl.attr('ik').get() == 1:
            # already in IK
            return

        # TODO: add support for joint-to-ctl offsets
        # TODO: incorporate delegate ctls into all 'move anim ctl here' functionality
        # move foot, and calculate new pole vector
        end_ik_move_ctl = IKFKControlUtils.getDelegateControl(end_ik_ctl)
        pulse.nodes.setWorldMatrix(end_ik_move_ctl, end_mtx)

        # move ik pole ctl
        new_pole_pos = IKFKControlUtils.calculateIKPoleControlLocation(
            mid_ik_ctl, root_mtx.translate, mid_mtx.translate, end_mtx.translate)
        mid_ik_ctl.setTranslation(new_pole_pos, space='world')

        root_ik_ctl.attr('ik').set(1)

    @staticmethod
    def getDelegateControl(node):
        ctl_delegate_data = meta.getMetaData(node, 'pulse_ctl_delegate')
        if ctl_delegate_data:
            return ctl_delegate_data['delegate_ctl']
        return node

    @staticmethod
    def calculateIKPoleControlLocation(ctl, root: pm.dt.Vector, mid: pm.dt.Vector, end: pm.dt.Vector):
        """
        Calculate the new position for an ik pole ctl given the matrices of the ikfk joints
        """
        pole_vector, pole_mid = pulse.joints.getIKPoleVectorAndMidPoint(root, mid, end)

        # calculate distance based on followers current location
        current_dist = pole_vector.dot(ctl.getTranslation(space='world') - pole_mid)

        # keep pole vector in front by at least 2x the distance from root to mid joint
        min_dist = 2 * (pm.dt.Vector(root) - pm.dt.Vector(mid)).length()
        dist = max(current_dist, min_dist)

        # calculate new pole position at the new distance
        return pole_mid + pole_vector * dist


class IKFKControlContextSubmenu(PulseNodeContextSubMenu):
    """
    Provides IKFK switching options on related controls.
    """

    @classmethod
    def shouldBuildSubMenu(cls, menu) -> bool:
        return cls.isNodeWithMetaClassSelected(IKFK_CONTROL_METACLASS)

    def buildMenuItems(self):
        pm.menuItem('Switch To FK', rp=self.getSafeRadialPosition('NW'), c=pm.Callback(self.switchToFKForSelected))
        pm.menuItem('Switch To IK', rp=self.getSafeRadialPosition('SW'), c=pm.Callback(self.switchToIKForSelected))

    def switchToIKForSelected(self):
        sel_ctls = self.getSelectedNodesWithMetaClass(IKFK_CONTROL_METACLASS)
        for ctl in sel_ctls:
            IKFKControlUtils.switchToIK(ctl)

    def switchToFKForSelected(self):
        sel_ctls = self.getSelectedNodesWithMetaClass(IKFK_CONTROL_METACLASS)
        for ctl in sel_ctls:
            IKFKControlUtils.switchToFK(ctl)
