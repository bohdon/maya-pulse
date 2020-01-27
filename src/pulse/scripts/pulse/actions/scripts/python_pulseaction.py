
import sys
import os
import imp
import pymel.core as pm

import pulse


class PythonAction(pulse.BuildAction):
    def validate(self):
        if not self.function:
            raise pulse.BuildActionError("function name cannot be empty")
        blueprintFile = pm.sceneName()
        if not blueprintFile:
            raise pulse.BuildActionError(
                "File is not saved, could not determine scripts file path")
        moduleFilepath = os.path.splitext(blueprintFile)[0] + '_scripts.py'
        if not os.path.isfile(moduleFilepath):
            raise pulse.BuildActionError(
                "Scripts file does not exist: %s" % moduleFilepath)

        func = self.importFunction(self.function, moduleFilepath)
        if func is None:
            raise pulse.BuildActionError(
                "function '%s' was not found in scripts file: %s" % (self.function, moduleFilepath))

    def run(self):
        blueprintFile = self.builder.blueprintFile
        if not blueprintFile:
            raise pulse.BuildActionError(
                "Failed to get blueprint file name from builder")

        moduleFilepath = os.path.splitext(blueprintFile)[0] + '_scripts.py'
        func = self.importFunction(self.function, moduleFilepath)
        func(self)

    def importFunction(self, functionName, moduleFilepath):
        """
        Import a module by full path, and return a function from the loaded module by name
        """
        moduleName = os.path.splitext(os.path.basename(moduleFilepath))[0]

        # delete the module if it already exists (so that it's reimported)
        if moduleName in sys.modules:
            del sys.modules[moduleName]

        module = imp.load_source(moduleName, moduleFilepath)

        if hasattr(module, functionName):
            attr = getattr(module, functionName)
            if callable(attr):
                return attr
