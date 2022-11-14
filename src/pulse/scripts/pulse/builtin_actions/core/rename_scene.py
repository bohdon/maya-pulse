import os

import pymel.core as pm

from pulse.core import BuildAction, BuildActionError, BlueprintSettings
from pulse.core import BuildActionAttributeType as AttributeType


class RenameSceneAction(BuildAction):
    """
    Rename the current scene for building. Should be performed before all other actions.

    Renaming the scene prevents accidentally saving the blueprint scene after failed builds
    or other modifications are made. The new scene acts as a sandbox for destructive operations
    and allows one-click re-opening of the blueprint scene in order to revert the build.
    """

    id = "Pulse.RenameScene"
    display_name = "Rename Scene"
    category = "Core"
    attr_definitions = [
        dict(
            name="filename",
            type=AttributeType.STRING,
            value="{rigName}_built",
            description="The new scene name. Can contain the {rigName} format key.",
        )
    ]

    def should_abort_on_error(self) -> bool:
        """
        Abort the build if this action fails to preserve the blueprint scene.
        """
        return True

    def run(self):
        scene_name = pm.sceneName()
        if not scene_name:
            raise BuildActionError("Scene is not saved.")

        rig_name = self.blueprint.get_setting(BlueprintSettings.RIG_NAME)
        if not rig_name:
            raise BuildActionError("No rig name was set.")

        file_name = self.filename.format(rigName=rig_name) + ".ma"
        file_path = os.path.join(os.path.dirname(scene_name), file_name)
        pm.renameFile(file_path)
