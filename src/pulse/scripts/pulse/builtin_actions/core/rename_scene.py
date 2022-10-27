import os

import pymel.core as pm

from pulse.build_items import BuildAction, BuildActionError
from pulse.build_items import BuildActionAttributeType as AttributeType


class RenameSceneAction(BuildAction):
    id = 'Pulse.RenameScene'
    display_name = 'Rename Scene'
    description = 'Renames the current scene so it can be saved to a different file.'
    category = 'Core'
    attr_definitions = [
        dict(name='filename', type=AttributeType.STRING, value='{rig[name]}_built',
             description="The new scene name, can contain format specifiers that accept the rig's meta data.")
    ]

    def validate(self):
        if not self.filename:
            raise BuildActionError('Filename cannot be empty')

    def run(self):
        scene_name = pm.sceneName()
        rig_data = self.get_rig_metadata()
        file_name = self.filename.format(rig=rig_data) + '.ma'
        file_path = os.path.join(os.path.dirname(scene_name), file_name)
        pm.renameFile(file_path)
