import logging
import os

from .version import __version__

LOG = logging.getLogger("pulse")
LOG.level = logging.DEBUG

# TODO: move all this actions logic to an actions module

BUILTIN_ACTIONS_LOADED = False


def load_actions_from_dir(start_dir: str):
    """
    Search for, load, and register build actions from a directory.

    Args:
        start_dir: str
            The directory to search for actions.
    """
    from .buildItems import BuildActionRegistry
    from .loader import BuildActionLoader

    loader = BuildActionLoader()
    for spec in loader.load_actions_from_dir(start_dir):
        BuildActionRegistry.get().register_action(spec)


def load_builtin_actions():
    """
    Load all built-in pulse actions.
    """
    global BUILTIN_ACTIONS_LOADED
    if not BUILTIN_ACTIONS_LOADED:
        actions_dir = os.path.join(os.path.dirname(__file__), 'actions')
        load_actions_from_dir(actions_dir)
        BUILTIN_ACTIONS_LOADED = True
