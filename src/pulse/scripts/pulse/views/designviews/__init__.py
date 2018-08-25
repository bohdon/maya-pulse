
from names import QuickNameEditor

def destroyEditorWorkspaceControls():
    """
    Development util to destroy workspace controls
    for all PulseWindows. Not intended for normal usage.
    """
    QuickNameEditor.destroyWindow()
