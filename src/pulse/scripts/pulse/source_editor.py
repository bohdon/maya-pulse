"""
Utils for launching source editors like VSCode or PyCharm.
"""

import os
import logging
import subprocess

from pulse.prefs import option_var_property

LOG = logging.getLogger(__name__)


def open_file(file_path: str):
    """
    Open a file in the current source editor.
    """
    launcher = SourceEditorLauncher()
    launcher.open_file(file_path)


def open_module(module):
    """
    Open a python module's file in the current source editor.

    Args:
        module:
            A python module to open.
    """
    launcher = SourceEditorLauncher()
    launcher.open_module(module)


class SourceEditorLauncher(object):
    """
    Handles running an editor to open and edit python source files.
    """

    # the name of the editor to use, can be the short name of an editor if in PATH, or the full path to one
    editor_path = option_var_property('pulse.editor.sourceEditorPath', 'pycharm.cmd')

    def set_editor_path(self, value):
        self.editor_path = value

    def _get_editor_path(self):
        """
        Return the executable of the current editor.
        """
        return self.editor_path

    def open_file(self, file_path):
        """
        Open a file in the source editor.

        Args:
            file_path: str
                The file to open in the editor.
        """
        if os.path.isfile(file_path):
            file_path = os.path.realpath(file_path)
        self._run(file_path)

    def open_module(self, module):
        """
        Open a python module's file in the source editor.

        Args:
            module:
                A python module to open.
        """
        if not hasattr(module, '__file__'):
            LOG.error('%s has no __file__ attribute.', module)
            return

        self.open_file(module.__file__)

    def _run(self, *args):
        """
        Launch the current editor with any args.
        """
        exec_name = self._get_editor_path()
        if not exec_name:
            LOG.error(f'No source editor was selected')
            return

        launch_args = [exec_name]
        launch_args.extend(args)

        LOG.info("Launching source editor: %s", ' '.join([str(a) for a in launch_args]))
        subprocess.Popen(launch_args)
