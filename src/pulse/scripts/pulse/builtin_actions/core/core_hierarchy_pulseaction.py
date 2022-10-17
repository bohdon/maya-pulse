import pymel.core as pm

import pulse.nodes
from pulse.buildItems import BuildAction
from pulse.buildItems import BuildActionAttributeType as AttrType


class BuildCoreHierarchyAction(BuildAction):
    """
    Builds a core hierarchy of the rig.

    This creates a group for one of the rig's main features (usually ctls, joints, or meshes)
    and parents the corresponding nodes.
    """

    id = 'Pulse.BuildCoreHierarchy'
    display_name = 'Build Core Hierarchy'
    description = 'Gathers nodes into a core hierarchy of the rig'
    category = 'Core'
    attr_definitions = [
        dict(name='groupName', type=AttrType.STRING,
             description="The name of the group. If left empty, will use the root node of the rig."),
        dict(name='groupVisible', type=AttrType.BOOL, value=True,
             description="Whether the group should be visible or not in the built rig."),
        dict(name='allNodes', type=AttrType.BOOL, value=False,
             description="If true, include all remaining unorganized nodes in this group."),
        dict(name='nodes', type=AttrType.NODE_LIST, optional=True,
             description="The nodes to include in this group."),
    ]

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
