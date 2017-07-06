
import pymel.core as pm

import pulse
import pulse.nodes


class BuildCoreHierarchyAction(pulse.BuildAction):
    """
    Builds the rigs core hierarchy.

    This creates a group for each of the rig's main
    features (usually ctls, joints, and meshes) and
    parents the corresponding nodes.
    """

    def run(self):
        grpData = dict()
        for grpName, nodes in self.groups.iteritems():
            grpNode = pm.group(name=grpName, em=True, p=self.rig)
            for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
                grpNode.attr(a).setLocked(True)
                grpNode.attr(a).setKeyable(False)

            # TODO: a way to make certain groups hidden

            # parent blueprint nodes for this group
            if len(nodes) > 0:
                tops = pulse.nodes.getParentNodes(nodes)
                if len(tops) > 0:
                    pm.parent(tops, grpNode)

            # add meta data to rig pointing to groups
            grpData[grpName] = grpNode

        self.updateRigMetaData({
            'groups':grpData,
        })
