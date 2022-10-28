[![Documentation Status](https://readthedocs.org/projects/maya-pulse/badge/?version=latest)](https://maya-pulse.readthedocs.io/en/latest/?badge=latest)

# Pulse

A rigging framework and toolkit built for Maya.

## Development Testing

Pulse is still in early development, but if you want to try it out here's the entry point commands I am currently using:

```python
# toggle the Pulse UI
import pulse.ui

pulse.ui.toggle_editor_ui()
```

```python
# development reload Pulse
import pymel.core as pm

try:
    import pulse.ui

    pulse.ui.tear_down_ui()
except:
    pass

# keep track of the current scene
scene_name = pm.sceneName()

pm.newFile(force=True)
pm.unloadPlugin('pulse')

try:
    pulse.ui.destroy_ui_model_instances()
except:
    pass

import pulse.vendor.mayacoretools as tools

tools.deleteModules('pulse*')

import pulse.ui

pulse.ui.show_editor_ui()

# re-open last scene
if scene_name:
    pm.openFile(scene_name)
```

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
