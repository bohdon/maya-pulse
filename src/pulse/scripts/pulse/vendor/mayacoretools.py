"""
A shared set of core tools for Maya.
"""

import sys
from fnmatch import fnmatch
import pymel.core as pm

__all__ = [
    'deleteModules',
    'preservedSelection',
]


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
        del sys.modules[mod]
    if verbose:
        print(f"Deleted {len(matching_mods)} sys module(s) matching {pattern}")


class preservedSelection(object):
    """
    Keeps the current selection for the scope of the given 'with' statement.
    """

    def __init__(self):
        self.selection = pm.selected()

    def __iter__(self):
        return iter(self.selection)

    def __len__(self):
        return len(self.selection)

    def __getitem__(self, key):
        return self.selection[key]

    def __setitem__(self, key, value):
        self.selection[key] = value

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        valid = [s for s in self.selection if s.exists()]
        pm.select(valid)
