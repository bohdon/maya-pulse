
import pymel.core as pm

import pulse
import pulse.joints
import pulse.nodes
import pulse.utilnodes


class ThreeBoneIKFKAction(pulse.BuildAction):

    def validate(self):
        if not self.endJoint:
            raise pulse.BuildActionError('endJoint is not set')
        if not self.rootCtl:
            raise pulse.BuildActionError('rootCtl is not set')
        if not self.midCtlIk:
            raise pulse.BuildActionError('midCtlIk is not set')
        if not self.midCtlFk:
            raise pulse.BuildActionError('midCtlFk is not set')
        if not self.endCtlIk:
            raise pulse.BuildActionError('endCtlIk is not set')
        if not self.endCtlFk:
            raise pulse.BuildActionError('endCtlFk is not set')

    def run(self):
        # retrieve mid and root joints
        self.midJoint = self.endJoint.getParent()
        self.rootJoint = self.midJoint.getParent()

        # duplicate joints for ik chain
        ikJointNameFmt = '{0}_ik'
        ikjnts = pulse.nodes.duplicateBranch(
            self.rootJoint, self.endJoint, nameFmt=ikJointNameFmt)
        for j in ikjnts:
            # TODO: debug settings for build actions
            j.v.set(True)
        self.rootIkJoint = ikjnts[0]
        self.midIkJoint = ikjnts[1]
        self.endIkJoint = ikjnts[2]

        # parent ik joints to root control
        self.rootIkJoint.setParent(self.rootCtl)

        # create ik and hook up pole object and controls
        handle, effector = pm.ikHandle(
            name="{0}_ikHandle".format(self.endIkJoint),
            startJoint=self.rootIkJoint,
            endEffector=self.endIkJoint,
            solver="ikRPsolver")

        # add twist attr to end control
        self.endCtlIk.addAttr('twist', at='double', k=1)
        self.endCtlIk.twist >> handle.twist

        # connect mid ik ctl (pole vector)
        pm.poleVectorConstraint(self.midCtlIk, handle)

        # parent ik handle to end control
        handle.setParent(self.endCtlIk)

        # constraint end joint scale and rotation to end control
        pm.orientConstraint(self.endCtlIk, self.endIkJoint, mo=True)
        pm.scaleConstraint(self.endCtlIk, self.endIkJoint, mo=True)

        # setup ikfk switch attr (integer, not blend)
        self.rootCtl.addAttr("ik", min=0, max=1, at='short',
                             defaultValue=1, keyable=1)
        ikAttr = self.rootCtl.attr("ik")

        # create target transforms driven by ikfk switching
        rootTargetName = n = '{}_ikfk_target'.format(self.rootJoint)
        rootTarget = pm.group(n=rootTargetName, em=True)
        midTargetName = n = '{}_ikfk_target'.format(self.midJoint)
        midTarget = pm.group(n=midTargetName, em=True)
        endTargetName = n = '{}_ikfk_target'.format(self.endJoint)
        endTarget = pm.group(n=endTargetName, em=True)

        # create choices for world matrix from ik and fk targets
        rootChoice = pulse.utilnodes.choice(
            ikAttr, self.rootCtl.wm, self.rootIkJoint.wm)
        midChoice = pulse.utilnodes.choice(
            ikAttr, self.midCtlFk.wm, self.midIkJoint.wm)
        endChoice = pulse.utilnodes.choice(
            ikAttr, self.endCtlFk.wm, self.endIkJoint.wm)

        pulse.utilnodes.decomposeMatrixAndConnect(
            rootChoice, rootTarget)
        pulse.utilnodes.decomposeMatrixAndConnect(
            midChoice, midTarget)
        pulse.utilnodes.decomposeMatrixAndConnect(
            endChoice, endTarget)

        pulse.nodes.fullConstraint(rootTarget, self.rootJoint)
        pulse.nodes.fullConstraint(midTarget, self.midJoint)
        pulse.nodes.fullConstraint(endTarget, self.endJoint)

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

        # cleanup
        handle.v.set(False)
        for jnt in ikjnts:
            # TODO: lock attrs
            jnt.v.set(False)
