[![Documentation Status](https://readthedocs.org/projects/maya-pulse/badge/?version=latest)](https://maya-pulse.readthedocs.io/en/latest/?badge=latest)

# Pulse

A rigging framework and toolkit built for Maya.

> Pulse is still in early development. Features may change without notice and backwards compatibility is not guaranteed.

## Adding Custom Actions

Actions are found by recursively searching a python package for `BuildAction` subclasses. Beyond the default
`pulse.builtin_actions`, you can add other action packages to search using the `BuildActionPackageRegistry`.

```py
from pulse.loader import BuildActionPackageRegistry
import my_pulse_actions

# register custom actions package
BuildActionPackageRegistry.get().add_package(my_pulse_actions)
```

In the above example, `my_pulse_actions` is a package with as many subpackages and submodules as you want.
As long as all modules are at least imported in the package, they and all `BuildAction` subclasses inside them will be
found.

```
my_pulse_actions/
  __init__.py (imports all submodules)
  my_custom_action.py
  deformers/
    __init__.py
    my_custom_deformer.py
```

You can dynamically import all your actions using `loader.import_all_submodules` to avoid maintaining package imports.

```py
# my_pulse_actions/__init__.py
from pulse import loader

# equivalent to:
#   import my_custom_action
#   import deformers.my_custom_deformer
loader.import_all_submodules(__name__)
```

## Roadmap

You can track development on Pulse [here](https://bohdon.notion.site/f656af523ead43a5893679d13e36e6aa).
