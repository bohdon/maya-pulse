import pymel.core as pm

import pulse.nodes
import pulse.spaces
from pulse.vendor import pymetanode as meta
from pulse.buildItems import BuildAction, BuildActionError
from pulse.ui.contextmenus import PulseNodeContextSubMenu


class CreateSpaceAction(BuildAction):

    def validate(self):
        if not self.node:
            raise BuildActionError("node must be set")
        if not self.name:
            raise BuildActionError("name cannot be empty")

    def run(self):
        pulse.spaces.createSpace(self.node, self.name)
        self.update_rig_metadata_dict('spaces', {self.name: self.node})


class SpaceConstrainAction(BuildAction):

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
            follower = pulse.nodes.createOffsetTransform(
                self.node, '{0}_spaceConstraint')
        # setup the constraint, which will be finalized during the ApplySpaces action
        pulse.spaces.setupSpaceConstraint(
            self.node, self.spaces, follower=follower, useOffsetMatrix=self.useOffsetMatrix)


class ApplySpacesAction(BuildAction):

    def validate(self):
        pass

    def run(self):
        if self.createWorldSpace:
            world_node = pm.group(name='world_space', empty=True, parent=self.rig)
            pulse.spaces.createSpace(world_node, 'world')
            self.update_rig_metadata_dict('spaces', {'world': world_node})

        # TODO: only gather not-yet-created constraints
        allConstraints = pulse.spaces.getAllSpaceConstraints()
        pulse.spaces.connectSpaceConstraints(allConstraints)


class SpaceSwitchUtils(object):
    @staticmethod
    def switchSpace(ctl: pm.PyNode, space: str) -> bool:
        """
        Switch a control into a new space

        Args:
            ctl: A node with space switching meta data
            space: The name of the space to switch to

        Returns:
            True if the space was changed, false otherwise
        """
        meta_data = meta.getMetaData(ctl, pulse.spaces.SPACECONSTRAINT_METACLASS)
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
        pulse.nodes.setWorldMatrix(ctl, wm)

        return True


class SpaceSwitchContextSubMenu(PulseNodeContextSubMenu):

    @classmethod
    def shouldBuildSubMenu(cls, menu) -> bool:
        # TODO: support switching multiple nodes if they have overlapping spaces
        return len(cls.getSelectedNodesWithMetaClass(pulse.spaces.SPACECONSTRAINT_METACLASS)) == 1

    def buildMenuItems(self):
        ctl = self.getSelectedNodesWithMetaClass(pulse.spaces.SPACECONSTRAINT_METACLASS)[0]
        meta_data = meta.getMetaData(ctl, pulse.spaces.SPACECONSTRAINT_METACLASS)
        spaces = meta_data.get('spaces', [])
        if spaces:
            pm.menuItem(l="Spaces", enable=False)
            for space in spaces:
                index = space['index']
                is_current = ctl.attr('space').get() == index

                title = pulse.names.toTitle(space['name'])
                suffix = ' (Default)' if index == 0 else ''
                prefix = '> ' if is_current else '    '
                display_name = f"{prefix}{title}{suffix}"

                pm.menuItem(l=display_name, c=pm.Callback(SpaceSwitchUtils.switchSpace, ctl, space['name']))
