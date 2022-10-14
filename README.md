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

Custom build actions can be added by registering a python package or directory. Actions are found by recursively
searching a directory and loading individual `*_pulseaction.py` modules that contain one or more `BuildAction`
subclasses. Add a custom actions directory during startup using the `BuildActionPackageRegistry`:

```py
# register a custom actions directory
from pulse.loader import BuildActionPackageRegistry

BuildActionPackageRegistry.get().add_dir('/path/to/my/actions')
```

An 'actions package' is just an empty python package whose location is used to find actions:

```py
# register a custom actions package
from pulse.loader import BuildActionPackageRegistry
from my_studio import my_pulse_actions

BuildActionPackageRegistry.get().add_package(my_pulse_actions)
```

## Roadmap

You can track development on Pulse [here](https://bohdon.notion.site/f656af523ead43a5893679d13e36e6aa).
