
import pymel.core as pm

import pulse
import pulse.nodes


class BuildCoreHierarchyAction(pulse.BuildAction):
    """
    Builds a core hierarchy of the rig.

    This creates a group for one of the rig's main
    features (usually ctls, joints, or meshes) and
    parents the corresponding nodes.
    """

    def run(self):

        grpNode = pm.group(name=self.groupName, em=True, p=self.rig)
        for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
            grpNode.attr(a).setLocked(True)
            grpNode.attr(a).setKeyable(False)

        if not self.groupVisible:
            grpNode.v.set(False)

        # parent blueprint nodes for this group
        if len(self.nodes) > 0:
            tops = pulse.nodes.getParentNodes(self.nodes)
            if len(tops) > 0:
                pm.parent(tops, grpNode)
