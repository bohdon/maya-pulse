
import os
import pymel.core as pm

import pulse


class RenameSceneAction(pulse.BuildAction):
    """
    Renames the current maya scene.
    """

    def validate(self):
        if not self.filename:
            raise pulse.BuildActionError('Filename cannot be empty')

    def run(self):
        sceneName = pm.sceneName()
        rigData = self.getRigMetaData()
        filename = self.filename.format(rig=rigData) + '.mb'
        newName = os.path.join(os.path.dirname(sceneName), filename)
        pm.renameFile(newName)
