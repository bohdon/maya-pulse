"""
Functionality for finding and loading Pulse Build Actions from a library of actions.
"""

import importlib
import logging
import os
import sys
import types
from fnmatch import fnmatch
from typing import List

from .actions import BuildAction, BuildActionSpec, BuildActionRegistry

__all__ = [
    "BuildActionLoader",
    "BuildActionPackageRegistry",
    "import_all_submodules",
    "load_actions",
    "reload_actions",
]

LOG = logging.getLogger(__name__)


def import_all_submodules(pkg_name: str):
    """
    Import all python modules within a package recursively.
    Used to make sure all build actions are loaded within an actions package
    so that they can be found by the loader.

    Designed to be called in the root __init__.py of every actions package:

        > from pulse import loader
        > loader.import_all_submodules(__name__)

    Args:
        pkg_name: The name of python package where everything will be imported
    """
    # get the full path to the pkg
    pkg_module = sys.modules[pkg_name]
    pkg_path = pkg_module.__path__[0]

    # find all __init__.py files recursively
    for base_dir, dir_names, file_names in os.walk(pkg_path):
        # potential name of a sub-package
        if os.path.basename(base_dir) in ("__pycache__",):
            continue

        sub_pkg_name = os.path.relpath(base_dir, pkg_path).replace("/", ".").replace("\\", ".")

        for file_name in file_names:
            if file_name in ("__init__.py", "__main__.py"):
                continue

            if fnmatch(file_name, "*.py"):
                module_name = os.path.splitext(file_name)[0]
                # leading dot to make sure it's a relative import to the root package
                sub_module_name = f".{sub_pkg_name}.{module_name}"
                importlib.import_module(sub_module_name, pkg_name)


def _is_same_python_file(path_a, path_b):
    return os.path.normpath(os.path.splitext(path_a)[0]) == os.path.normpath(os.path.splitext(path_b)[0])


def load_actions():
    """
    Load all available pulse actions.
    """
    BuildActionPackageRegistry.get().load_actions()


def reload_actions():
    """
    Clear all loaded actions from the registry and load actions again.
    """
    BuildActionPackageRegistry.get().reload_actions()


class BuildActionPackageRegistry(object):
    """
    A registry of packages where actions should be loaded.
    Also keeps track of whether all packages have been loaded, and can reload packages when necessary.
    """

    # the shared registry instance, accessible from `BuildActionPackageRegistry.get()`
    _instance = None

    @classmethod
    def get(cls):
        """
        Return the main BuildActionPackageRegistry
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # map of all registered actions by id
        self._registered_actions: dict[str, BuildActionSpec] = {}
        # list of python packages containing pulse actions to load.
        self.action_packages = []
        # whether to include the builtin pulse actions package or not
        self.use_builtin_actions = True
        # true if the packages in this registry have been loaded
        self.has_loaded_actions = False

        if self.use_builtin_actions:
            self._add_builtin_actions()

    def _add_builtin_actions(self):
        from .. import builtin_actions

        self.add_package(builtin_actions)

    def add_package(self, package, reload=False):
        """
        Add an actions package to the registry.
        Does not load the actions, intended to be called during startup.
        """
        if package not in self.action_packages:
            self.action_packages.append(package)

        if reload:
            self.reload_actions()

    def remove_all(self, reload=False):
        self.action_packages = []

        if self.use_builtin_actions:
            self._add_builtin_actions()

        if reload:
            self.reload_actions()

    def load_actions(self):
        """
        Load all available pulse actions.
        """
        if self.has_loaded_actions:
            return

        loader = BuildActionLoader()

        # load actions by package
        for package in self.action_packages:
            loader.load_actions_from_package(package)

        self.has_loaded_actions = True

    def reload_actions(self):
        """
        Clear all loaded actions from the registry and load actions again.
        """
        BuildActionRegistry.get().remove_all()
        self.has_loaded_actions = False
        self.load_actions()


class BuildActionLoader(object):
    """
    Handles finding and loading Build Action modules and returning them as BuildActionSpec objects.
    They can then be registered with the build action registry for use.
    """

    def __init__(self, use_registry=True):
        # if true, automatically register loaded actions, otherwise just return them
        self.use_registry = use_registry

    def load_actions_from_package(self, package: types.ModuleType) -> List[BuildActionSpec]:
        """
        Recursively find all pulse actions in a python package.
        Searches BuildAction subclasses recursively in all submodules.
        Automatically register each spec if `self.use_registry` is True.

        Args:
            package: A python package containing BuildActions
        """
        LOG.info("Loading Pulse actions from package: %s", package)

        return self._load_actions_from_module(package)

    def _load_actions_from_module(self, module: types.ModuleType) -> List[BuildActionSpec]:
        """
        Perform the actual recursive loading of actions within a package or module.
        """
        LOG.debug("Loading actions from module: %s", module)

        action_specs: List[BuildActionSpec] = []
        for name in dir(module):
            obj = getattr(module, name)

            if self._is_submodule(obj, module):
                # recursively load submodule
                action_specs.extend(self._load_actions_from_module(obj))

            elif self._is_valid_build_action_class(obj):
                # load BuildAction subclass
                action_spec = BuildActionSpec(obj, module)
                action_specs.append(action_spec)
                LOG.debug("Loaded BuildAction: %s", action_spec)

        if self.use_registry:
            self.register_actions(action_specs)

        return action_specs

    def _is_module(self, obj) -> bool:
        return isinstance(obj, types.ModuleType)

    def _is_submodule(self, obj, parent_module) -> bool:
        parent_name = parent_module.__name__
        if self._is_module(obj):
            if obj.__name__ == parent_module.__name__:
                return False
            if not obj.__package__:
                return False
            # add trailing . to ensure it's not some similarly named sibling
            return obj.__package__ == parent_name or obj.__package__.startswith(f"{parent_name}.")

    def register_actions(self, action_specs: List[BuildActionSpec]):
        """
        Register action specs with the shared registry.
        """
        for action_spec in action_specs:
            BuildActionRegistry.get().add_action(action_spec)

    @staticmethod
    def _is_valid_build_action_class(obj) -> bool:
        """
        Return true if an object is a valid BuildAction subclass.
        """
        return isinstance(obj, type) and issubclass(obj, BuildAction) and obj is not BuildAction
