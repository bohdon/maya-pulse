import logging
import os
from typing import Optional

# TODO: remove maya dependencies from this core module, add BlueprintBuilder subclass that uses maya progress bars
import pymel.core as pm

from ..vendor import yaml
from .. import version
from .serializer import PulseDumper, PulseLoader, UnsortableOrderedDict
from .build_items import BuildStep

__all__ = [
    "Blueprint",
    "BlueprintFile",
    "BlueprintSettings",
]

LOG = logging.getLogger(__name__)

BLUEPRINT_VERSION = version.__version__


def get_default_config_file() -> str:
    """
    Return the path to the default blueprint config file
    """
    pulse_dir = os.path.dirname(version.__file__)
    return os.path.realpath(os.path.join(pulse_dir, "config/default_blueprint_config.yaml"))


def load_default_config() -> Optional[dict]:
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


class BlueprintSettings(object):
    """
    Constants defining the keys for Blueprint settings.
    """

    RIG_NAME = "rigName"
    RIG_NODE_NAME_FORMAT = "rigNodeNameFormat"
    DEBUG_BUILD = "debugBuild"


class Blueprint(object):
    """
    A Blueprint contains all the information necessary to build
    a full rig. It is essentially made up of configuration settings
    and an ordered hierarchy of BuildActions.
    """

    @staticmethod
    def from_data(data) -> "Blueprint":
        """
        Create a Blueprint instance from serialized data
        """
        blueprint = Blueprint()
        blueprint.deserialize(data)
        return blueprint

    def __init__(self):
        # various settings used by the blueprint, such as the rig name
        self.settings = {}
        self.add_missing_settings()
        # the version of this blueprint
        self.version: str = BLUEPRINT_VERSION
        # the root step of this blueprint
        self.rootStep: BuildStep = BuildStep("Root")
        # the config file to use when designing this Blueprint
        self.config_file_path: str = get_default_config_file()
        # the config, automatically loaded when calling `get_config`
        self._config: Optional[dict] = None

    def add_missing_settings(self):
        """
        Add new or missing settings to the Blueprint, do not overwrite any existing settings.
        """
        if BlueprintSettings.RIG_NAME not in self.settings:
            self.set_setting(BlueprintSettings.RIG_NAME, "")
        if BlueprintSettings.RIG_NODE_NAME_FORMAT not in self.settings:
            self.set_setting(BlueprintSettings.RIG_NODE_NAME_FORMAT, "{rigName}_rig")
        if BlueprintSettings.DEBUG_BUILD not in self.settings:
            self.set_setting(BlueprintSettings.DEBUG_BUILD, False)

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

    def serialize(self) -> UnsortableOrderedDict:
        data = UnsortableOrderedDict()
        data["version"] = self.version
        data["settings"] = self.settings
        data["steps"] = self.rootStep.serialize()
        return data

    def deserialize(self, data: dict) -> bool:
        """
        Returns:
            True if the data was deserialized successfully
        """
        self.version = data.get("version", None)
        self.settings = data.get("settings", {})
        self.rootStep.deserialize(data.get("steps", {"name": "Root"}))
        # inject new or missing settings
        self.add_missing_settings()
        return True

    def load_from_file(self, file_path: str) -> bool:
        """
        Returns:
            True if the load was successful
        """
        LOG.debug("Loading blueprint: %s", file_path)

        try:
            with open(file_path, "r") as fp:
                data = yaml.load(fp, Loader=PulseLoader)
        except IOError:
            return False

        if not data:
            return False

        return self.deserialize(data)

    def save_to_file(self, file_path: str) -> bool:
        """
        Returns:
            True if the save was successful
        """
        LOG.info("Saving blueprint: %s", file_path)

        data = self.serialize()
        with open(file_path, "w") as fp:
            yaml.dump(data, fp, default_flow_style=False, Dumper=PulseDumper)

        return True

    def dump_yaml(self) -> str:
        data = self.serialize()
        return yaml.dump(data, default_flow_style=False, Dumper=PulseDumper)

    def load_from_yaml(self, yaml_str: str) -> bool:
        """
        Load this Blueprint from a yaml string
        """
        try:
            data = yaml.load(yaml_str, Loader=PulseLoader)
        except Exception:
            return False

        if not data:
            return False

        return self.deserialize(data)

    def get_step_by_path(self, path: str) -> BuildStep:
        """
        Return a BuildStep from the Blueprint by path

        Args:
            path: str
                A path pointing to a BuildStep, e.g. 'My/Build/Step'
        """
        if not path:
            return self.rootStep
        else:
            step = self.rootStep.get_child_by_path(path)
            if not step:
                LOG.warning("Could not find BuildStep: %s", path)
            return step

    def add_default_actions(self):
        """
        Add a set of core BuildActions to the blueprint.
        """
        rename_action = BuildStep(action_id="Pulse.RenameScene")
        import_action = BuildStep(action_id="Pulse.ImportReferences")
        hierarchy_action = BuildStep(action_id="Pulse.BuildCoreHierarchy")
        hierarchy_attr = hierarchy_action.action_proxy.get_attr("allNodes")
        if hierarchy_attr:
            hierarchy_attr.set_value(True)
        main_group = BuildStep("Main")
        self.rootStep.add_children(
            [
                rename_action,
                import_action,
                hierarchy_action,
                main_group,
            ]
        )

    def get_config(self) -> dict:
        """
        Return the config for this Blueprint.
        Load the config from disk if it hasn't been loaded yet.
        """
        if self._config is None and self.config_file_path:
            self.load_config()
        return self._config

    def load_config(self):
        """
        Load the config for this Blueprint from the current file path.
        Reloads the config even if it is already loaded.
        """
        if self.config_file_path:
            self._config = _load_config(self.config_file_path)


class BlueprintFile(object):
    """
    Contains a Blueprint and file path info for saving and loading, as well as
    tracking modification status.

    A Blueprint File is considered valid by default, even without a file path,
    just like a new 'untitled' maya scene file. A file path must be assigned before it
    can be saved.
    """

    # the file extension to use for blueprint files
    file_ext: str = "yml"

    def __init__(self, file_path: Optional[str] = None, is_read_only: bool = False):
        self.blueprint = Blueprint()
        self.file_path = file_path
        self.is_read_only = is_read_only
        self._is_modified = False

    def has_file_path(self) -> bool:
        return bool(self.file_path)

    def can_load(self) -> bool:
        return self.has_file_path()

    def can_save(self) -> bool:
        return self.has_file_path() and not self.is_read_only

    def is_modified(self) -> bool:
        return self._is_modified

    def modify(self):
        """
        Mark the blueprint file as modified.
        """
        self._is_modified = True

    def clear_modified(self):
        """
        Clear the modified status of the file.
        """
        self._is_modified = False

    def get_file_name(self) -> Optional[str]:
        """
        Return the base name of the file path.
        """
        if self.file_path:
            return os.path.basename(self.file_path)

    def save(self) -> bool:
        """
        Save the Blueprint to file.

        Returns:
            True if the file was saved successfully.
        """
        if not self.file_path:
            LOG.warning("Cant save Blueprint, file path is not set.")
            return False

        success = self.blueprint.save_to_file(self.file_path)

        if success:
            self.clear_modified()
        else:
            LOG.error("Failed to save Blueprint to file: %s", self.file_path)

        return success

    def save_as(self, file_path: str) -> bool:
        """
        Save the Blueprint with a new file path.
        """
        self.file_path = file_path
        return self.save()

    def load(self) -> bool:
        """
        Load the blueprint from file.
        """
        if not self.file_path:
            LOG.warning("Cant load Blueprint, file path is not set.")
            return False

        if not os.path.isfile(self.file_path):
            LOG.warning("Blueprint file does not exist: %s", self.file_path)
            return False

        success = self.blueprint.load_from_file(self.file_path)

        if success:
            self.clear_modified()
        else:
            LOG.error("Failed to load Blueprint from file: %s", self.file_path)

        return success

    def resolve_file_path(self, allow_existing=False):
        """
        Automatically resolve the current file path based on the open maya scene.
        Does nothing if file path is already set.

        Args:
            allow_existing: bool
                If true, allow resolving to a path that already exists on disk.
        """
        if not self.file_path:
            file_path = self.get_default_file_path()
            if file_path:
                if allow_existing or not os.path.isfile(file_path):
                    self.file_path = file_path

    def get_default_file_path(self) -> Optional[str]:
        """
        Return the file path to use for a new blueprint file.
        Uses the open maya scene by default.

        # TODO: move out of core into a maya specific subclass
        """
        scene_name = pm.sceneName()

        if scene_name:
            base_name = os.path.splitext(scene_name)[0]
            return f"{base_name}.{self.file_ext}"
