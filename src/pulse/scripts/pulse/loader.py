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
from . import builtin_actions

LOG = logging.getLogger(__name__)


def _is_same_python_file(path_a, path_b):
    return (os.path.normpath(os.path.splitext(path_a)[0]) ==
            os.path.normpath(os.path.splitext(path_b)[0]))


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
    A registry of packages or directories where actions should be loaded.
    Also keeps track of whether the packages have been loaded, and can reload packages when necessary.
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
        # list of directories containing pulse actions to load.
        self.action_dirs = []
        # whether to include the builtin pulse actions package or not
        self.use_builtin_actions = True
        # true if the packages in this registry have been loaded
        self.has_loaded_actions = False

        if self.use_builtin_actions:
            self.add_package(builtin_actions)

    def add_package(self, package, reload=False):
        """
        Add an actions package to the registry.
        Does not load the actions, intended to be called during startup.

        Action modules are not connected to the package, but are instead imported individually and dynamically.
        The package itself is simply used to locate the directory where the actions can be found.
        """
        if package not in self.action_packages:
            self.action_packages.append(package)

        if reload:
            self.reload_actions()

    def add_dir(self, actions_dir, reload=False):
        """
        Add an actions directory actions to the registry.
        Does not load the actions, intended to be called during startup.
        """
        if actions_dir not in self.action_dirs:
            self.action_dirs.append(actions_dir)

        if reload:
            self.reload_actions()

    def remove_all(self, reload=False):
        self.action_packages = []
        self.action_dirs = []

        if self.use_builtin_actions:
            self.add_package(builtin_actions)

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

        # load actions by dir
        for actions_dir in self.action_dirs:
            loader.load_actions_from_dir(actions_dir)

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
        paths = getattr(package, '__path__', None)
        if not paths:
            LOG.warning(f'load_actions_from_package: {package} is not a valid python package')
            return []

        path = paths[0]
        LOG.info(f'Loading Pulse actions from package: {package.__name__} ({path})...')

        start_dir = os.path.dirname(path)
        return self._load_actions_from_dir(start_dir)

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

        LOG.info(f'Loading Pulse actions from directory: {start_dir}...')

        return self._load_actions_from_dir(start_dir)

    def _load_actions_from_dir(self, start_dir: str) -> List[BuildActionSpec]:
        """
        The internal load actions from dir that operates recursively.
        Doesn't perform initial path handling and logging. `start_dir` must be valid.
        """
        if not os.path.isdir(start_dir):
            raise ValueError(f'{start_dir} not found')

        result: List[BuildActionSpec] = []

        paths = os.listdir(start_dir)
        for path in paths:
            full_path = os.path.join(start_dir, path)

            if os.path.isfile(full_path):
                if fnmatch(path, self.file_pattern):
                    module = self._import_module_from_file(full_path)
                    result.extend(self.load_actions_from_module(module))

            elif os.path.isdir(full_path):
                result.extend(self._load_actions_from_dir(full_path))

        return result

    def register_actions(self, action_specs: List[BuildActionSpec]):
        """
        Register action specs with the shared registry.
        """
        for action_spec in action_specs:
            BuildActionRegistry.get().add_action(action_spec)

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
