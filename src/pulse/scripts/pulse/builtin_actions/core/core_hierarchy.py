import pymel.core as pm

from pulse import nodes
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
            grp_node = pm.group(name=self.groupName, em=True, p=self.rig)
            for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
                grp_node.attr(a).setLocked(True)
                grp_node.attr(a).setKeyable(False)

            # only modify group visibility if a new group was created
            if not self.groupVisible:
                grp_node.v.set(False)

        else:
            grp_node = self.rig

        # parent nodes to this group
        all_nodes = self.nodes

        if not all_nodes:
            all_nodes = self.get_unorganized_nodes()

        if all_nodes:
            tops = nodes.getParentNodes(all_nodes)
            if len(tops) > 0:
                pm.parent(tops, grp_node)

    def get_unorganized_nodes(self):
        """
        Return all nodes in the scene that aren't already
        in the rig, and aren't default scene nodes.
        """

        def should_include(node):
            # filter out default cameras
            if node.numChildren() == 1 and len(node.getShapes(typ='camera')) == 1:
                return False
            return True

        all_nodes: list[pm.nt.Transform] = pm.ls(assemblies=True)
        if self.rig in all_nodes:
            all_nodes.remove(self.rig)
        all_nodes = [n for n in all_nodes if should_include(n)]
        return all_nodes
