"""
Functionality for finding and loading Pulse Build Actions from a library of actions.
"""

import importlib
import logging
import os
import sys
from fnmatch import fnmatch
from typing import List

from .buildItems import BuildAction, BuildActionSpec, BuildActionRegistry
from .vendor import yaml

LOG = logging.getLogger(__name__)

HAS_LOADED_BUILTIN_ACTIONS = False


def _is_same_python_file(path_a, path_b):
    return (os.path.normpath(os.path.splitext(path_a)[0]) ==
            os.path.normpath(os.path.splitext(path_b)[0]))


def load_actions():
    """
    Load all available pulse actions.
    """
    # TODO: add extensible action packages list to include
    load_builtin_actions()


def load_builtin_actions():
    """
    Load all built-in pulse actions.
    """
    from . import builtin_actions

    global HAS_LOADED_BUILTIN_ACTIONS
    if not HAS_LOADED_BUILTIN_ACTIONS:
        loader = BuildActionLoader()
        loader.load_actions_from_package(builtin_actions)
        HAS_LOADED_BUILTIN_ACTIONS = True


class BuildActionLoader(object):
    """
    Handles finding and loading Build Action configs and modules and returning
    them as BuildActionSpec objects. They can then be registered with the
    build action registry for use.
    """

    def __init__(self, use_registry=True):
        # if true, automatically register loaded actions, otherwise just return them
        self.use_registry = use_registry
        # the action module name format to match against
        self.file_pattern = '*_pulseaction.py'
        # the action config file extension to search for
        self.config_extension = 'yaml'

    def load_actions_from_module(self, module) -> List[BuildActionSpec]:
        """
        Find all BuildAction subclasses in a module, load associated config data for them,
        and return a list of BuildActionConfigs with the results.

        Args:
            module:
                A single pulse actions python module that contains one or more Build Actions.

        Returns:
            A list of BuildActionSpec for each Build Action class and corresponding
            yml config in the module.
        """
        config_file_path = f'{os.path.splitext(module.__file__)[0]}.{self.config_extension}'
        action_configs = self._load_config(config_file_path)

        action_specs: List[BuildActionSpec] = []
        for name in dir(module):
            obj = getattr(module, name)

            if self._is_valid_build_action_class(obj):
                # get config for the action class
                action_config = action_configs.get(name, {})
                if action_config:
                    action_spec = BuildActionSpec(action_config, config_file_path, obj, module)
                    LOG.debug('Loaded BuildAction: %s', action_spec)
                    action_specs.append(action_spec)
                else:
                    LOG.error("Build Action config key '%s' was not found in: %s", name, config_file_path)

        if self.use_registry:
            self.register_actions(action_specs)

        return action_specs

    def load_actions_from_package(self, package) -> List[BuildActionSpec]:
        """
        Recursively find all pulse actions in a python package's directory.
        Searches for python modules by matching against a file name pattern.

        Args:
            package:
                A python package used to locate the actions directory.
        """
        if not hasattr(package, '__file__'):
            LOG.warning(f'load_actions_from_package: {package} is not a valid python package')
            return []

        start_dir = os.path.dirname(package.__file__)
        return self.load_actions_from_dir(start_dir)

    def load_actions_from_dir(self, start_dir: str) -> List[BuildActionSpec]:
        """
        Recursively load all build actions in a directory.
        Searches for python modules by matching against a file name pattern.

        Args:
            start_dir: str
                The directory to search for actions.

        Returns:
            A list of BuildActionConfigs representing the loaded config and BuildAction class.
        """
        if '~' in start_dir:
            start_dir = os.path.expanduser(start_dir)

        if not os.path.isdir(start_dir):
            LOG.warning("Pulse actions directory not found: %s", start_dir)
            return []

        result: List[BuildActionSpec] = []

        paths = os.listdir(start_dir)
        for path in paths:
            full_path = os.path.join(start_dir, path)

            if os.path.isfile(full_path):
                if fnmatch(path, self.file_pattern):
                    module = self._import_module_from_file(full_path)
                    result.extend(self.load_actions_from_module(module))

            elif os.path.isdir(full_path):
                result.extend(self.load_actions_from_dir(full_path))

        return result

    def register_actions(self, action_specs: List[BuildActionSpec]):
        """
        Register action specs with the shared registry.
        """
        for action_spec in action_specs:
            BuildActionRegistry.get().register_action(action_spec)

    def _load_config(self, config_file_path) -> dict:
        """
        Load a build action config file. Note that an action config file may contain
        config entries for multiple build actions.
        """
        if not os.path.isfile(config_file_path):
            LOG.error("Config file not found: %s", config_file_path)
            return {}

        with open(config_file_path, 'r') as fp:
            config = yaml.load(fp.read())

        return config

    def _import_module_from_file(self, file_path: str):
        """
        Import and return a python module from a file path.

        If the module is already found in sys modules it will be deleted to force a reload.

        """
        # get module name
        name = os.path.splitext(os.path.basename(file_path))[0]

        # check for existing module in sys.modules
        if name in sys.modules:
            if _is_same_python_file(sys.modules[name].__file__, file_path):
                # correct module already imported, delete it to force reload
                del sys.modules[name]
            else:
                raise ImportError(f"BuildAction module does not have a unique module name: {file_path}")

        # add dir to sys path if necessary
        dir_name = os.path.dirname(file_path)
        is_not_in_sys_path = False

        if dir_name not in sys.path:
            sys.path.insert(0, dir_name)
            is_not_in_sys_path = True

        try:
            # TODO(bsayre): error handling of import?
            module = importlib.import_module(name)
        except:
            LOG.error("Failed to import Build Action module: %s", name)
            pass
        else:
            return module
        finally:
            # remove path from sys
            if is_not_in_sys_path:
                sys.path.remove(dir_name)

    @staticmethod
    def _is_valid_build_action_class(obj) -> bool:
        """
        Return true if an object is a valid BuildAction subclass.
        """
        return isinstance(obj, type) and issubclass(obj, BuildAction) and obj is not BuildAction
