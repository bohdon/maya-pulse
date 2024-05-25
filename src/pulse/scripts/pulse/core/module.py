from __future__ import annotations

import logging
from enum import Enum

import pymel.core as pm

from pulse.core.actions import BuildStep
from pulse.core.asset import PulseAsset
from pulse.core.serializer import UnsortableOrderedDict

LOG = logging.getLogger(__name__)

__all__ = [
    "BlueprintBase",
    "BlueprintModule",
]


class BlueprintBase(PulseAsset):
    """
    Base class for a blueprint object that contains a list of build steps,
    and is associated with a specific Maya scene file.
    """

    def __init__(self, file_path: str = None, is_read_only=False):
        super().__init__(file_path=file_path, is_read_only=is_read_only)
        # the root step of this module
        self.root_step: BuildStep = BuildStep("Root")
        # the maya scene file associated with this module
        self.scene_path: str | None = None

    def get_step_by_path(self, path: str) -> BuildStep:
        """
        Return a BuildStep from the Blueprint by path

        Args:
            path: A path pointing to a BuildStep, e.g. '/My/Build/Step'
        """
        if not path or path == "/":
            return self.root_step
        else:
            step = self.root_step.get_child_by_path(path)
            if step:
                return step
            else:
                LOG.warning("Could not find BuildStep: %s", path)

    def set_scene_path_to_current(self):
        """
        Update the associated scene path to the currently open Maya scene.
        """
        self.scene_path = str(pm.sceneName())

    def _serialize(self) -> UnsortableOrderedDict:
        data = super()._serialize()
        data["steps"] = self.root_step.serialize()
        data["scene_path"] = self.scene_path
        return data

    def _deserialize(self, data: dict):
        super()._deserialize(data)
        self.root_step.deserialize(data.get("steps", {"name": "Root"}))
        self.scene_path = data.get("scene_path", "")


class BlueprintModuleVersion(Enum):
    INITIAL = 0

    LATEST = INITIAL


class BlueprintModule(BlueprintBase):
    """
    A module represents a related unit of a rig, and contains
    an ordered list of build actions. Modules can represent a spine, arm, leg,
    or other reusable components that can be combined to form a full rig.
    """

    def __init__(self):
        super().__init__()
        self.version = BlueprintModuleVersion.LATEST.value

    def post_load(self):
        super().post_load()

        self.version = BlueprintModuleVersion.LATEST.value
