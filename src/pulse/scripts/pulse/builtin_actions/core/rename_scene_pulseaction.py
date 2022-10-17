import os

import pymel.core as pm

from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttributeType


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
        sceneName = pm.sceneName()
        rigData = self.get_rig_metadata()
        filename = self.filename.format(rig=rigData) + '.ma'
        newName = os.path.join(os.path.dirname(sceneName), filename)
        pm.renameFile(newName)
