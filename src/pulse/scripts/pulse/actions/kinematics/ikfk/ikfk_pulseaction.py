
import pymel.core as pm

import pulse
import pulse.nodes
import pulse.joints


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
        if not self.endCtl:
            raise pulse.BuildActionError('endCtl is not set')

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
            n="{0}_ikHandle".format(self.endIkJoint),
            sj=self.rootIkJoint, ee=self.endIkJoint, sol="ikRPsolver")

        # add twist attr to end control
        self.endCtl.addAttr('twist', at='double', k=1)
        self.endCtl.twist >> handle.twist

        # connect mid ik ctl (pole vector)
        pm.poleVectorConstraint(self.midCtlIk, handle)

        # parent ik handle to end control
        handle.setParent(self.endCtl)

        # constraint end joint scale and rotation to end control
        pm.orientConstraint(self.endCtl, self.endIkJoint, mo=True)
        pm.scaleConstraint(self.endCtl, self.endIkJoint, mo=True)

        # constraint the original joint branch to the ik joint branch
        pulse.nodes.fullConstraint(self.rootIkJoint, self.rootJoint)
        pulse.nodes.fullConstraint(self.midIkJoint, self.midJoint)
        pulse.nodes.fullConstraint(self.endIkJoint, self.endJoint)

        # setup ikfk switch
        # ...

        # cleanup
        for jnt in ikjnts:
            # TODO: lock attrs
            jnt.v.set(False)

        handle.v.set(False)
