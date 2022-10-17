"""
The built-in Pulse actions package.
"""

from pulse import loader

# dynamically import all subpackages and submodules recursively so that
# actions can be easily added and removed without having to maintain package imports
loader.import_all_submodules(__name__)
