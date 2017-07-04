
import sys
import os
import importlib
from fnmatch import fnmatch

from . import core


__all__ = [
    'BuildActionLoader',
]


def _isSamePythonFile(fileA, fileB):
    return os.path.normpath(os.path.splitext(fileA)[0]) == os.path.normpath(os.path.splitext(fileB)[0])

class BuildActionLoader(object):

    def loadActionsFromModule(self, module):
        """
        Return BuildItem type map data for all BuildActions
        contained in the given module
        """
        result = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, core.BuildAction) and obj is not core.BuildAction:
                result.append(obj)
        return result

    def loadActionsFromDirectory(self, startDir, pattern='*_action.py'):
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
        # check for existing module in sys.modules.
        # we usually dont want one to exist, so we can import and then erase it
        if name in sys.modules:
            if _isSamePythonFile(sys.modules[name].__file__, filePath):
                # module already imported, we'll take it
                return sys.modules[name]
            else:
                raise ImportError("BuildAction module does not have a unique module name: " + filePath)
        # add dir to sys path if necessary
        dirName = os.path.dirname(filePath)
        isNotInSysPath = False
        if not dirName in sys.path:
            sys.path.insert(0, dirName)
            isNotInSysPath = True
        module = importlib.import_module(name)
        # remove module and path from sys
        del sys.modules[name]
        if isNotInSysPath:
            sys.path.remove(dirName)
        return module
