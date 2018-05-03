
import sys
import os
import logging
import importlib
from fnmatch import fnmatch
import pulse.vendor.yaml as yaml

from . import core


__all__ = [
    'BuildActionLoader',
]

LOG = logging.getLogger(__name__)


def _isSamePythonFile(fileA, fileB):
    return (os.path.normpath(os.path.splitext(fileA)[0]) ==
            os.path.normpath(os.path.splitext(fileB)[0]))


class BuildActionLoader(object):

    def loadConfig(self, actionClass, module):
        """
        Load the config data for a BuildAction class.

        Args:
            actionClass (BuildAction): The action for which to load a config
            module (module): The module that contains the BuildAction class

        Returns:
            True if config was loaded successfully
        """
        if actionClass.config is not None:
            # TODO: validate the config
            return True

        configFile = os.path.splitext(module.__file__)[0] + '.yaml'
        if not os.path.isfile(configFile):
            LOG.warning("Config file not found: {0}".format(configFile))
            return False

        with open(configFile, 'rb') as fp:
            config = yaml.load(fp.read())

        # get config for the BuildAction by class name
        if config and actionClass.__name__ in config:
            # assign the config to the class
            actionClass.config = config[actionClass.__name__]
            actionClass.configFile = configFile
            return True
        else:
            LOG.warning("Config data {0} not found in {1}".format(
                actionClass.__name__, configFile))
            return False

    def loadActionsFromModule(self, module):
        """
        Return BuildItem type map data for all BuildActions
        contained in the given module
        """
        result = []
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and issubclass(obj, core.BuildAction) and
                    obj is not core.BuildAction):
                # load config data onto the class
                if self.loadConfig(obj, module):
                    LOG.debug('Loaded BuildAction: {0}'.format(obj.getTypeName()))
                    result.append(obj)
                else:
                    LOG.error('Failed to load BuildAction: {0}'.format(
                        obj.getTypeName()))
        return result

    def loadActionsFromDirectory(self, startDir, pattern='*_pulseaction.py'):
        """
        Return BuildItem type map data for all BuildActions found
        by searching a directory. Search is performed recursively for
        any python files matching a pattern.

        Args:
            startDir: A str path of the directory to search
        """
        if '~' in startDir:
            startDir = os.path.expanduser(startDir)

        result = []

        paths = os.listdir(startDir)
        for path in paths:
            fullPath = os.path.join(startDir, path)

            if os.path.isfile(fullPath):
                if fnmatch(path, pattern):
                    module = self._getModuleFromFile(fullPath)
                    result.extend(self.loadActionsFromModule(module))

            elif os.path.isdir(fullPath):
                result.extend(self.loadActionsFromDirectory(fullPath, pattern))

        return result

    def _getModuleFromFile(self, filePath):
        # get module name
        name = os.path.splitext(os.path.basename(filePath))[0]
        # check for existing module in sys.modules
        if name in sys.modules:
            if _isSamePythonFile(sys.modules[name].__file__, filePath):
                # correct module already imported, delete it to force reload
                del sys.modules[name]
            else:
                raise ImportError("BuildAction module does not have "
                                  "a unique module name: " + filePath)
        # add dir to sys path if necessary
        dirName = os.path.dirname(filePath)
        isNotInSysPath = False
        if not dirName in sys.path:
            sys.path.insert(0, dirName)
            isNotInSysPath = True
        module = importlib.import_module(name)
        # remove path from sys
        if isNotInSysPath:
            sys.path.remove(dirName)
        return module
