import pymel.core as pm

from pulse import names, nodes, spaces
from pulse.vendor import pymetanode as meta
from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType
from pulse.ui.contextmenus import PulseNodeContextSubMenu


class CreateSpaceAction(BuildAction):
    id = 'Pulse.CreateSpace'
    display_name = 'Create Space'
    description = 'Create a Space that can be used for dynamic constraints'
    color = (.4, .42, .8)
    category = 'Spaces'
    sort_order = 0

    attr_definitions = [
        dict(name='node', type=AttrType.NODE),
        dict(name='name', type=AttrType.STRING),
    ]

    def validate(self):
        if not self.node:
            raise BuildActionError("node must be set")
        if not self.name:
            raise BuildActionError("name cannot be empty")

    def run(self):
        spaces.create_space(self.node, self.name)
        self.update_rig_metadata_dict('spaces', {self.name: self.node})


class SpaceConstrainAction(BuildAction):
    id = 'Pulse.SpaceConstrain'
    display_name = 'Space Constrain'
    description = 'Creates a dynamic constraint to one or more defined spaces'
    color = (.4, .42, .8)
    category = 'Spaces'
    sort_order = 1

    attr_definitions = [
        dict(name='node', type=AttrType.NODE),
        dict(name='spaces', type=AttrType.STRING_LIST),
        dict(name='useOffsetMatrix', type=AttrType.BOOL, value=True,
             description="If true, constrain the node using offsetParentMatrix, "
                         "and avoid creating anextra offset transform.")
    ]

    def get_min_api_version(self):
        if self.useOffsetMatrix:
            return 20200000
        return 0

    def validate(self):
        if not self.node:
            raise BuildActionError("node must be set")
        if not self.spaces:
            raise BuildActionError("spaces must have at least one value")

    def run(self):
        follower = None
        if not self.useOffsetMatrix:
            # create an offset transform to be constrained
            follower = nodes.create_offset_transform(self.node, '{0}_spaceConstraint')
        # set up the constraint, which will be finalized during the ApplySpaces action
        spaces.setup_space_constraint(self.node, self.spaces, follower=follower, use_offset_matrix=self.useOffsetMatrix)


class ApplySpacesAction(BuildAction):
    id = 'Pulse.ApplySpaces'
    display_name = 'Apply Spaces'
    description = 'Resolves and connects all Space Constraints in the rig'
    color = (.4, .42, .8)
    category = 'Spaces'
    sort_order = 2

    attr_definitions = [
        dict(name='createWorldSpace', type=AttrType.BOOL, value=True,
             description="Automatically create a 'world' space node.")
    ]

    def validate(self):
        pass

    def run(self):
        if self.createWorldSpace:
            world_node = pm.group(name='world_space', empty=True, parent=self.rig)
            spaces.create_space(world_node, 'world')
            self.update_rig_metadata_dict('spaces', {'world': world_node})

        # TODO: only gather not-yet-created constraints
        all_constraints = spaces.get_all_space_constraints()
        spaces.connect_space_constraints(all_constraints)


class SpaceSwitchUtils(object):
    @staticmethod
    def switch_space(ctl: pm.PyNode, space: str) -> bool:
        """
        Switch a control into a new space

        Args:
            ctl: A node with space switching metadata
            space: The name of the space to switch to

        Returns:
            True if the space was changed, false otherwise
        """
        meta_data = meta.getMetaData(ctl, spaces.SPACE_CONSTRAINT_METACLASS)
        space_data = [s for s in meta_data.get('spaces', []) if s['name'] == space]
        if not space_data:
            return False

        space_data = space_data[0]
        index = space_data['index']

        # remember world matrix
        wm = ctl.wm.get()
        # change space
        ctl.attr('space').set(index)
        # restore world matrix
        nodes.set_world_matrix(ctl, wm)

        return True


class SpaceSwitchContextSubMenu(PulseNodeContextSubMenu):

    @classmethod
    def shouldBuildSubMenu(cls, menu) -> bool:
        # TODO: support switching multiple nodes if they have overlapping spaces
        return len(cls.getSelectedNodesWithMetaClass(spaces.SPACE_CONSTRAINT_METACLASS)) == 1

    def buildMenuItems(self):
        ctl = self.getSelectedNodesWithMetaClass(spaces.SPACE_CONSTRAINT_METACLASS)[0]
        meta_data = meta.getMetaData(ctl, spaces.SPACE_CONSTRAINT_METACLASS)
        all_spaces = meta_data.get('spaces', [])
        if all_spaces:
            pm.menuItem(l="Spaces", enable=False)
            for space in all_spaces:
                index = space['index']
                is_current = ctl.attr('space').get() == index

                title = names.to_title(space['name'])
                suffix = ' (Default)' if index == 0 else ''
                prefix = '> ' if is_current else '    '
                display_name = f"{prefix}{title}{suffix}"

                pm.menuItem(l=display_name, c=pm.Callback(SpaceSwitchUtils.switch_space, ctl, space['name']))
