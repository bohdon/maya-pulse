import pymel.core as pm

import pulse.nodes
from pulse.vendor import pymetanode as meta
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType
from pulse.animinterface import ANIM_CTL_METACLASS
from pulse.ui.contextmenus import PulseNodeContextSubMenu

try:
    import resetter
except ImportError:
    resetter = None


class AnimControlAction(BuildAction):
    id = 'Pulse.AnimControl'
    display_name = 'Anim Control'
    description = 'Configures a node to be used as an animation control'
    color = (.85, .65, .4)
    category = 'Controls'
    attr_definitions = [
        dict(name='controlNode', type=AttrType.NODE, description="The control node to mark as an animation control"),
        dict(name='zeroOutMethod', type=AttrType.OPTION, value=1, options=[
            'None',
            'Offset Matrix',
            'Insert Transform',
        ], description="Which method to use to ensure the control transform attributes are zeroed by"
                       "default in the current possition"),
        dict(name='keyableAttrs', type=AttrType.STRING_LIST, value=['t', 'r', 's'], canMirror=False,
             description='Defines attributes that can be animated. All others will be locked.'),
    ]

    def get_min_api_version(self):
        if self.zeroOutMethod == 1:
            return 20200000
        return 0

    def validate(self):
        if not self.controlNode:
            raise BuildActionError('controlNode is not set')

    def run(self):
        # add metaclass to the control, making it
        # easy to search for by anim tools, etc
        meta.setMetaData(self.controlNode, ANIM_CTL_METACLASS, {})

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
        self.extend_rig_metadata_list('animControls', [self.controlNode])


class AnimControlContextSubMenu(PulseNodeContextSubMenu):
    """
    Context menu for working with animation controls.
    """

    @classmethod
    def shouldBuildSubMenu(cls, menu) -> bool:
        return cls.isNodeWithMetaClassSelected(ANIM_CTL_METACLASS)

    def buildMenuItems(self):
        pm.menuItem(l='Reset', rp=self.getSafeRadialPosition('N'), c=pm.Callback(self.resetSelected))

    def resetSelected(self):
        if resetter:
            sel_ctls = self.getSelectedNodesWithMetaClass(ANIM_CTL_METACLASS)
            if sel_ctls:
                resetter.reset(sel_ctls)
