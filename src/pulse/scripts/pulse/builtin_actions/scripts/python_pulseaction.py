import os
import re
import sys
from importlib.machinery import SourceFileLoader

import pymel.core as pm

from pulse.buildItems import BuildAction, BuildActionError
from pulse.vendor.Qt import QtWidgets
from pulse.ui.actioneditor import BuildActionProxyForm
from pulse import sourceeditor

# template for a new script file
SCRIPT_TEMPLATE = """\"""
Script file for a python Pulse action.
\"""
from pulse.buildItems import BuildAction
"""

# template for a function added to the script file automatically
FUNCTION_TEMPLATE = """

def {functionName}(action: BuildAction):
    print(action.rig)
    print(action.nodes)
"""


class PythonAction(BuildAction):

    def validate(self):
        # TODO: remove since required attributes should be handled generally instead of in each actions validate()
        if not self.function:
            raise BuildActionError("function name is required")

        scene_file_name = pm.sceneName()
        if not scene_file_name:
            raise BuildActionError("File is not saved, could not determine scripts file path")

        module_filepath = os.path.splitext(scene_file_name)[0] + '_scripts.py'

        if not os.path.isfile(module_filepath):
            raise BuildActionError(f"Scripts file does not exist: {module_filepath}")

        func = self.import_function(self.function, module_filepath)
        if func is None:
            raise BuildActionError(
                "function '%s' was not found in scripts file: %s" % (self.function, module_filepath))

    def run(self):
        # TODO: use actual blueprint file, not maya scene
        scene_file_path = self.builder.scene_file_path
        if not scene_file_path:
            raise BuildActionError("Failed to get blueprint file name from builder")

        module_file_path = os.path.splitext(scene_file_path)[0] + '_scripts.py'
        func = self.import_function(self.function, module_file_path)
        func(self)

    def import_function(self, function_name, module_file_path):
        """
        Import a module by full path, and return a function from the loaded module by name
        """
        module_name = os.path.splitext(os.path.basename(module_file_path))[0]

        # delete the module if it already exists (so that it's re-imported)
        if module_name in sys.modules:
            del sys.modules[module_name]

        module = SourceFileLoader(module_name, module_file_path).load_module()

        if hasattr(module, function_name):
            attr = getattr(module, function_name)
            if callable(attr):
                return attr


class PythonActionForm(BuildActionProxyForm):

    def setupLayoutHeader(self, parent, layout):
        edit_btn = QtWidgets.QPushButton(parent)
        edit_btn.setText("Edit Script")
        edit_btn.clicked.connect(self.openScriptFileInEditor)
        layout.addWidget(edit_btn)

    def openScriptFileInEditor(self):
        sceneName = pm.sceneName()
        if not sceneName:
            pm.warning('Save the Maya scene to enable script editing')
            return

        actionProxy = self.getActionProxy()
        functionName = actionProxy.get_attr('function').get_value()
        if not functionName:
            pm.warning('Set a function name first')

        filePath = os.path.splitext(sceneName)[0] + '_scripts.py'

        # create file if it doesn't exist with the function stubbed in for convenience
        if not os.path.isfile(filePath):
            self.createScriptFile(filePath, functionName)

        # add function to the script automatically if it doesn't exist
        self.addFunctionToScriptFile(filePath, functionName)

        sourceeditor.open_file(filePath)

    def createScriptFile(self, filePath: str, functionName: str):
        """
        Create the scripts file and add some boilerplate code.
        """
        content = SCRIPT_TEMPLATE.format(functionName=functionName)

        with open(filePath, 'w') as fp:
            fp.write(content)

    def addFunctionToScriptFile(self, filePath: str, functionName: str):
        """
        Add a function to the script file automatically. Does nothing if the function already exists.
        """
        with open(filePath, 'r') as fp:
            content = fp.read()

        func_pattern = re.compile(fr'^def {functionName}\(.*$', re.M)
        if func_pattern.search(content):
            # function already exists
            return

        # append function to end of file
        new_content = FUNCTION_TEMPLATE.format(functionName=functionName)
        with open(filePath, 'a') as fp:
            fp.write(new_content)
