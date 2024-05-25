from __future__ import annotations

import logging
import os
from enum import Enum

from pulse.core.serializer import PulseLoader, PulseDumper, UnsortableOrderedDict
from pulse.vendor import yaml

LOG = logging.getLogger(__name__)

__all__ = [
    "PulseAsset",
]


class PulseAssetVersion(Enum):
    NONE = 0


class PulseAsset(object):
    """
    Base class for an object that can be serialized to data or a file.
    """

    # the file extension to use for assets
    file_ext: str = "yml"

    def __init__(self, file_path: str = None, is_read_only=False):
        # the file path for this asset
        self.file_path = file_path
        # is the asset read only?
        self.is_read_only = is_read_only
        # is the asset currently modified?
        self._is_modified = False
        # the version of this asset
        self.version: int = PulseAssetVersion.NONE.value
        # the yaml loader class to use for this asset
        self._loader_class = PulseLoader
        # the yaml dumper class to use for this asset
        self._dumper_class = PulseDumper

    def get_name(self) -> str:
        """
        Return the name of this asset.
        """
        raise NotImplementedError

    def serialize(self) -> UnsortableOrderedDict:
        """
        Serialize the asset to a dict object.
        """
        self.pre_save()
        return self._serialize()

    def _serialize(self) -> UnsortableOrderedDict:
        data = UnsortableOrderedDict()
        data["version"] = self.version
        return data

    def serialize_yaml(self) -> str:
        """
        Serialize the asset to a yaml string.
        """
        data = self.serialize()
        return yaml.dump(data, default_flow_style=False, Dumper=self._dumper_class)

    def deserialize(self, data: dict):
        """
        Deserialize the asset from a dict object.
        """
        self._deserialize(data)
        self.post_load()

    def _deserialize(self, data: dict):
        self.version = data.get("version", PulseAssetVersion.NONE.value)

    def deserialize_yaml(self, yaml_str: str):
        """
        Deserialize the object from a yaml string.
        """
        try:
            data = yaml.load(yaml_str, Loader=self._loader_class)
        except Exception:
            pass
        else:
            if data:
                self.deserialize(data)

    def pre_save(self):
        """
        Called just before serializing the asset to data.
        """
        pass

    def post_load(self):
        """
        Called after the asset has been deserialized from data.
        """
        pass

    def save(self) -> bool:
        """
        Save the asset to disk.

        Returns:
            True if the save was successful.
        """
        if not self.has_file_path():
            LOG.info("Cant save asset %s, file path is not set", self)
            return False

        LOG.info("Saving %s: %s", self, self.file_path)

        contents = self.serialize_yaml()

        try:
            with open(self.file_path, "w") as fp:
                fp.write(contents)
        except IOError:
            return False
        else:
            self.clear_modified()
            return True

    def save_as(self, file_path: str) -> bool:
        """
        Save the Blueprint with a new file path.
        """
        self.file_path = file_path
        return self.save()

    def load(self) -> bool:
        """
        Load the asset from a file.

        Returns:
            True if the load was successful
        """
        if not self.has_file_path():
            LOG.info("Cant load asset %s, file path is not set", self)
            return False

        if not os.path.isfile(self.file_path):
            LOG.warning("Cant load asset %s, file does not exist: %s", self.file_path)
            return False

        LOG.info("Loading %s: %s", self, self.file_path)

        try:
            with open(self.file_path, "r") as fp:
                contents = fp.read()
        except IOError:
            return False
        else:
            self.deserialize_yaml(contents)
            return True

    def has_file_path(self) -> bool:
        return bool(self.file_path)

    def get_file_name(self) -> str | None:
        """
        Return the base name of the file path.
        """
        if self.file_path:
            return os.path.basename(self.file_path)

    def can_load(self) -> bool:
        """
        Return true if the asset has a valid existing file path
        """
        return self.has_file_path() and os.path.isfile(self.file_path)

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
