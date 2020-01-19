
import pymel.core as pm
import pymetanode as meta

import pulse
import pulse.nodes


class AnimControlAction(pulse.BuildAction):

    def run(self):
        # add meta class to the control, making it
        # easy to search for by anim tools, etc
        meta.setMetaData(self.controlNode, self.config['controlMetaClass'], {})

        if self.zeroOutMethod == 1:
            # freeze transforms
            pm.makeIdentity(self.controlNode, apply=True, n=0,
                            pn=True, r=True, t=True, s=True)
        elif self.zeroOutMethod == 2:
            # create an offset
            offsetNode = pulse.nodes.createOffsetGroup(self.controlNode)

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
