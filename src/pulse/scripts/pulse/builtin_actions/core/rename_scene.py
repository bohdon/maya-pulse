import os

import pymel.core as pm

from pulse.core import BuildAction, BuildActionError, BlueprintSettings
from pulse.core import BuildActionAttributeType as AttributeType

from . import COLOR, CATEGORY


class RenameSceneAction(BuildAction):
    """
    Rename the current scene for building. Should be performed before all other actions.

    Renaming the scene prevents accidentally saving the blueprint scene after failed builds
    or other modifications are made. The new scene acts as a sandbox for destructive operations
    and allows one-click re-opening of the blueprint scene in order to revert the build.
    """

    id = "Pulse.RenameScene"
    display_name = "Rename Scene"
    color = COLOR
    category = CATEGORY
    attr_definitions = [
        dict(
            name="filename",
            type=AttributeType.STRING,
            value="{scene_name}_built",
            description="The new scene name. Will provide the {scene_name} format key with the current scene name.",
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

        file_name = self.filename.format(scene_name=scene_name) + ".ma"
        file_path = os.path.join(os.path.dirname(scene_name), file_name)
        pm.renameFile(file_path)
