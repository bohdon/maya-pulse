from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Optional

# TODO: remove maya dependencies from this core module, add BlueprintBuilder subclass that uses maya progress bars
import pymel.core as pm

from . import PulseAsset
from .config import PulseConfig
from .module import BlueprintBase, BlueprintModule
from .serializer import UnsortableOrderedDict
from .. import version
from ..vendor import yaml

__all__ = [
    "Blueprint",
    "BlueprintSettings",
]

LOG = logging.getLogger(__name__)


class BlueprintVersion(Enum):
    INITIAL = 0
    PULSE_ASSETS = 1

    LATEST = PULSE_ASSETS


def get_default_config_file() -> str:
    """
    Return the path to the default blueprint config file
    """
    pulse_dir = os.path.dirname(version.__file__)
    return os.path.realpath(os.path.join(pulse_dir, "config/default_blueprint_config.yaml"))


def load_default_config() -> dict | None:
    """
    Load and return the default blueprint config
    """
    return _load_config(get_default_config_file())


def _load_config(file_path) -> Optional[dict]:
    """
    Load and return the contents of a yaml config file
    """
    if not os.path.isfile(file_path):
        LOG.warning("Config file not found: %s", file_path)
        return

    with open(file_path, "r") as fp:
        return yaml.safe_load(fp)


class BlueprintSettings(dict):
    """
    Constants defining the keys for Blueprint settings.
    """

    RIG_NAME = "rigName"
    RIG_NODE_NAME_FORMAT = "rigNodeNameFormat"
    DEBUG_BUILD = "debugBuild"

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.clear()
        self[BlueprintSettings.RIG_NAME] = ""
        self[BlueprintSettings.RIG_NODE_NAME_FORMAT] = "{rigName}_rig"
        self[BlueprintSettings.DEBUG_BUILD] = False


class Blueprint(BlueprintBase):
    """
    A Blueprint contains all the information necessary to build
    a full rig. It is made up of one or more BlueprintModules and a config.
    """

    def __init__(self, file_path: str = None, is_read_only=False):
        super().__init__(file_path=file_path, is_read_only=is_read_only)
        # asset version
        self.version = BlueprintVersion.LATEST.value
        # various settings used by the blueprint, such as the rig name
        self.settings = BlueprintSettings()
        # the config for this blueprint
        self.config = PulseConfig(get_default_config_file())

    def get_setting(self, key: str, default=None):
        """
        Return a Blueprint setting by key.
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value):
        """
        Set a Blueprint setting by key.
        """
        self.settings[key] = value

    def pre_save(self):
        super().pre_save()
        self.set_scene_path_to_current()

    def post_load(self):
        super().post_load()
        self.version = BlueprintVersion.LATEST.value

    def _serialize(self) -> UnsortableOrderedDict:
        data = super()._serialize()
        data["settings"] = self.settings
        return data

    def _deserialize(self, data: dict):
        super()._deserialize(data)
        self.settings.reset()
        self.settings.update(data.get("settings", {}))
        return True

    def reset_to_default(self):
        """
        Reset the Blueprint to the default set of actions.
        """
        default_data = self.config.get("default_blueprint", {})
        self.deserialize(default_data)
        self.modify()
