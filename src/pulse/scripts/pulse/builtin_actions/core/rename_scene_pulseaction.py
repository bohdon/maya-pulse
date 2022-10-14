import os

import pymel.core as pm

from pulse.buildItems import BuildAction, BuildActionError


class RenameSceneAction(BuildAction):
    """
    Renames the current maya scene.
    """

    def validate(self):
        if not self.filename:
            raise BuildActionError('Filename cannot be empty')

    def run(self):
        sceneName = pm.sceneName()
        rigData = self.get_rig_metadata()
        filename = self.filename.format(rig=rigData) + '.ma'
        newName = os.path.join(os.path.dirname(sceneName), filename)
        pm.renameFile(newName)