"""
A shared set of core tools for Maya.
"""

import sys
import os
from fnmatch import fnmatch


def deleteModules(pattern, verbose=True):
    """
    Delete all existing python modules that match
    the given pattern.

    Args:
        pattern: A str pattern to match against module names
        verbose: A bool, when true, prints each module that is deleted
    """
    mods = sys.modules.keys()
    matching_mods = [mod for mod in mods if fnmatch(mod, pattern)]
    for mod in matching_mods:
        if verbose:
            print('Deleting module: {0}'.format(mod))
        del sys.modules[mod]
