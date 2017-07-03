
from .version import *
from .core import *
from .loader import *

def loadActionsFromDirectory(startDir):
    """
    Search for and load BuildActions from the given directory,
    then register them for use.

    Args:
        startDir: A str path of the directory to search
    """
    loader = BuildActionLoader()
    actions = loader.loadActionsFromDirectory(startDir)
    registerActions(actions)