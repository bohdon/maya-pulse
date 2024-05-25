from __future__ import annotations

import logging
import os

from pulse.vendor import yaml

LOG = logging.getLogger(__name__)

__all__ = [
    "PulseConfig",
]


class PulseConfig(dict):
    """
    Base class for a config file object.
    """

    def __init__(self, file_path: str | None = None, auto_load=True):
        super().__init__()

        # the file path to the config
        self.file_path = file_path

        # has the config ever been loaded?
        self._is_loaded = False

        if auto_load:
            self.load()

    def load(self, force=False):
        """
        Load and update this config object with the contents of a yaml config file
        """
        if self._is_loaded and not force:
            return

        if not os.path.isfile(self.file_path):
            LOG.warning("Config file not found: %s", self.file_path)
            return

        with open(self.file_path, "r") as fp:
            content = yaml.safe_load(fp)

        self.clear()
        self.update(content)
