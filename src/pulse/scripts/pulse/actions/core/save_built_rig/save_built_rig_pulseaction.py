
import os
import tempfile
import pymel.core as pm

import pulse


class SaveBuiltRigAction(pulse.BuildAction):
    """
    Performs the main saving operation after a rig
    has been built.
    """

    def run(self):
    	sceneName = pm.sceneName()
        rigData = self.getRigMetaData()
    	# save to temp location and open
    	tempPath = os.path.join(tempfile.gettempdir(), 'pulse_built_rig_temp.mb')
        pm.select(self.rig)
        pm.exportSelected(tempPath, type='mayaBinary', force=True)
        pm.openFile(tempPath, force=True)
        # rename opened file, but don't save
        filename = self.filename.format(rig=rigData) + '.mb'
        newName = os.path.join(os.path.dirname(sceneName), filename)
        pm.renameFile(newName)