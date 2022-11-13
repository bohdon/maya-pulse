"""
The built-in Pulse actions package.
"""

from pulse.core import import_all_submodules

# dynamically import all subpackages and submodules recursively so that
# actions can be easily added and removed without having to maintain package imports
import_all_submodules(__name__)
