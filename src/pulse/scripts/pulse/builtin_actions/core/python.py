import os
import re
import sys
from importlib.machinery import SourceFileLoader

import pymel.core as pm

from pulse.core import BuildAction, BuildActionError
from pulse.core import BuildActionAttributeType as AttrType
from pulse.vendor.Qt import QtWidgets
from pulse.ui.action_editor import BuildActionProxyForm
from pulse import source_editor

from . import COLOR, CATEGORY

# template for a new script file
SCRIPT_TEMPLATE = """\"""
Script file for a python Pulse action.
\"""
from pulse.core import BuildAction
"""

# template for a function added to the script file automatically
FUNCTION_TEMPLATE = """

def {function_name}(action: BuildAction):
    print(action.rig)
    print(action.nodes)
"""


class PythonActionForm(BuildActionProxyForm):
    """
    Custom build action form that displays a button for quickly opening the python script
    in a source editor.

    See :class:`~pulse.source_editor.SourceEditorLauncher` for more info on launching an editor.
    """

    def setup_layout_header(self, parent, layout):
        edit_btn = QtWidgets.QPushButton(parent)
        edit_btn.setText("Edit Script")
        edit_btn.clicked.connect(self._open_script_file_in_editor)
        layout.addWidget(edit_btn)

    def _open_script_file_in_editor(self):
        scene_name = pm.sceneName()
        if not scene_name:
            pm.warning("Save the Maya scene to enable script editing")
            return

        action_proxy = self.get_action_proxy()
        function_name = action_proxy.get_attr("function").get_value()
        if not function_name:
            pm.warning("Set a function name first")

        file_path = os.path.splitext(scene_name)[0] + "_scripts.py"

        # create file if it doesn't exist with the function stubbed in for convenience
        if not os.path.isfile(file_path):
            self._create_script_file(file_path, function_name)

        # add function to the script automatically if it doesn't exist
        self._add_function_to_script_file(file_path, function_name)

        source_editor.open_file(file_path)

    def _create_script_file(self, file_path: str, function_name: str):
        """
        Create the scripts file and add some boilerplate code.
        """
        content = SCRIPT_TEMPLATE.format(function_name=function_name)

        with open(file_path, "w") as fp:
            fp.write(content)

    def _add_function_to_script_file(self, file_path: str, function_name: str):
        """
        Add a function to the script file automatically. Does nothing if the function already exists.
        """
        with open(file_path, "r") as fp:
            content = fp.read()

        func_pattern = re.compile(rf"^def {function_name}\(.*$", re.M)
        if func_pattern.search(content):
            # function already exists
            return

        # append function to end of file
        new_content = FUNCTION_TEMPLATE.format(function_name=function_name)
        with open(file_path, "a") as fp:
            fp.write(new_content)


class PythonAction(BuildAction):
    """
    Run a python script.

    Looks for a script file in the same directory as the blueprint, and executes
    a specific function by name.

    **Example script file:**

    .. code-block:: python

        from pulse.core import BuildAction

        def my_function(action: BuildAction):
            print(action.rig)
            print(action.nodes)
    """

    id = "Pulse.Python"
    display_name = "Python"
    color = COLOR
    category = CATEGORY
    editor_form_class = PythonActionForm
    attr_definitions = [
        dict(
            name="function",
            type=AttrType.STRING,
            value="my_function",
            description="The name of the function to run. Should accept a single argument for the"
            "BuildAction being run.",
        ),
        dict(
            name="nodes",
            type=AttrType.NODE_LIST,
            optional=True,
            description="An optional list of nodes to pass in as arguments to the script.",
        ),
    ]

    def validate(self):
        blueprint_file_path = self.builder.blueprint_file.file_path
        if not blueprint_file_path:
            self.logger.error("Blueprint is not saved, could not determine script file path.")
            return

        module_file_path = os.path.splitext(blueprint_file_path)[0] + "_scripts.py"

        if not os.path.isfile(module_file_path):
            self.logger.error(f"Script file does not exist: {module_file_path}.")
            return

        func = self._import_function(self.function, module_file_path)
        if func is None:
            self.logger.error("Function '%s' was not found.", self.function)

    def run(self):
        blueprint_file_path = self.builder.blueprint_file.file_path
        if not blueprint_file_path:
            raise BuildActionError("Failed to get blueprint file path from builder.")

        module_file_path = os.path.splitext(blueprint_file_path)[0] + "_scripts.py"
        func = self._import_function(self.function, module_file_path)
        func(self)

    def _import_function(self, function_name, module_file_path):
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
