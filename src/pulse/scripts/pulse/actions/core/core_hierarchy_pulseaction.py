import pymel.core as pm

import pulse.nodes
from pulse.core.buildItems import BuildAction


class BuildCoreHierarchyAction(BuildAction):
    """
    Builds a core hierarchy of the rig.

    This creates a group for one of the rig's main
    features (usually ctls, joints, or meshes) and
    parents the corresponding nodes.
    """

    def run(self):
        if self.groupName:
            grpNode = pm.group(name=self.groupName, em=True, p=self.rig)
            for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
                grpNode.attr(a).setLocked(True)
                grpNode.attr(a).setKeyable(False)

            # only modify group visibility if a new group was created
            if not self.groupVisible:
                grpNode.v.set(False)

        else:
            grpNode = self.rig

        # parent nodes to this group
        nodes = self.nodes

        if not nodes:
            nodes = self.getUnorganizedNodes()

        if nodes:
            tops = pulse.nodes.getParentNodes(nodes)
            if len(tops) > 0:
                pm.parent(tops, grpNode)

    def getUnorganizedNodes(self):
        """
        Return all nodes in the scene that aren't already
        in the rig, and aren't default scene nodes.
        """

        def shouldInclude(node):
            # filter out default cameras
            if node.numChildren() == 1 and len(node.getShapes(typ='camera')) == 1:
                return False
            return True

        nodes = pm.ls(assemblies=True)
        if self.rig in nodes:
            nodes.remove(self.rig)
        nodes = [n for n in nodes if shouldInclude(n)]
        return nodes
