
from layout import LayoutLinkEditorWindow

def destroyEditorWorkspaceControls():
    """
    Development util to destroy workspace controls
    for all PulseWindows. Not intended for normal usage.
    """
    LayoutLinkEditorWindow.destroyWindow()
