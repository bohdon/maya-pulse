
import sys
import os
import imp
import subprocess
import pymel.core as pm
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

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


class PythonActionForm(pulse.views.BuildActionProxyForm):

    def setupLayoutHeader(self, parent, layout):
        editBtn = QtWidgets.QPushButton(parent)
        editBtn.setText("Edit Script")
        editBtn.clicked.connect(self.openScriptFileInEditor)
        layout.addWidget(editBtn)

    def openScriptFileInEditor(self):
        if not 'VSCODE_PATH' in os.environ:
            pm.warning(
                'Add VSCODE_PATH to environment to enable script editing')
            return

        vscode = os.environ['VSCODE_PATH']
        sceneName = pm.sceneName()
        if not sceneName:
            pm.warning('Save the scene to enable script editing')
            return

        scriptsFilename = os.path.splitext(sceneName)[0] + '_scripts.py'
        subprocess.Popen([vscode, scriptsFilename])
