
import pulse


class BuildCoreHierarchyAction(pulse.BuildAction):
    """
    Builds the rigs core hierarchy.

    This creates a group for each of the rig's main
    features (usually ctls, joints, and meshes) and
    parents the corresponding nodes.
    """

    def run(self):
        pass