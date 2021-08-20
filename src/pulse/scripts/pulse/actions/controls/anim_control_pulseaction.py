import pymel.core as pm

import pulse.nodes
import pymetanode as meta
from pulse.buildItems import BuildAction, BuildActionError
from pulse.views.contextmenus import PulseNodeContextSubMenu

try:
    import resetter
except ImportError:
    resetter = None

# TODO: move config into python, so this doesn't have to be defined twice
# the meta class for anim controls, should match controlMetaClass in the action config
ANIM_CTL_METACLASS = 'pulse_animcontrol'


class AnimControlAction(BuildAction):

    def getMinApiVersion(self):
        if self.zeroOutMethod == 1:
            return 20200000
        return 0

    def validate(self):
        if not self.controlNode:
            raise BuildActionError('controlNode is not set')

    def run(self):
        # add meta class to the control, making it
        # easy to search for by anim tools, etc
        meta.setMetaData(self.controlNode, self.config['controlMetaClass'], {})

        if self.zeroOutMethod == 1:
            # freeze offset matrix
            pulse.nodes.freezeOffsetMatrix(self.controlNode)
        elif self.zeroOutMethod == 2:
            # create an offset transform
            pulse.nodes.createOffsetTransform(self.controlNode)

        # lockup attributes
        keyableAttrs = pulse.nodes.getExpandedAttrNames(self.keyableAttrs)
        lockedAttrs = pulse.nodes.getExpandedAttrNames(
            ['t', 'r', 'rp', 's', 'sp', 'ra', 'sh', 'v'])
        lockedAttrs = list(set(lockedAttrs) - set(keyableAttrs))

        for attrName in keyableAttrs:
            attr = self.controlNode.attr(attrName)
            attr.setKeyable(True)

        for attrName in lockedAttrs:
            attr = self.controlNode.attr(attrName)
            attr.setKeyable(False)
            attr.showInChannelBox(False)
            attr.setLocked(True)

        # show rotate order in channel box
        self.controlNode.rotateOrder.setLocked(True)
        self.controlNode.rotateOrder.showInChannelBox(True)

        # update rig meta data
        self.extendRigMetaDataList('animControls', [self.controlNode])

        # set defaults for all keyable attributes
        if resetter:
            resetter.setDefaults(self.controlNode)


class AnimControlContextSubMenu(PulseNodeContextSubMenu):
    """
    Context menu for working with animation controls.
    """

    @classmethod
    def shouldBuildSubMenu(cls, menu) -> bool:
        # TODO: get access to config here, or move config into python for easier use
        return cls.isNodeWithMetaClassSelected([ANIM_CTL_METACLASS])

    def buildMenuItems(self):
        pm.menuItem(l='Reset', rp=self.getSafeRadialPosition('N'), c=pm.Callback(self.resetSelected))

    def resetSelected(self):
        if resetter:
            sel_ctls = self.getSelectedNodesWithMetaClass([ANIM_CTL_METACLASS])
            if sel_ctls:
                resetter.reset(sel_ctls)
