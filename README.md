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

Actions are found by recursively searching a directory and loading individual `*_pulseaction.py` modules that contain
one or more `BuildAction` subclasses. You can add additional actions directories to search during startup using
the `BuildActionPackageRegistry`:

```py
# register a custom actions directory
from pulse.loader import BuildActionPackageRegistry

BuildActionPackageRegistry.get().add_dir('/path/to/my/actions')
```

You can also use a python package, whose location will be used as the directory to search:

```py
# register a custom actions package
from pulse.loader import BuildActionPackageRegistry
import my_pulse_actions

BuildActionPackageRegistry.get().add_package(my_pulse_actions)
```

In the above example, `my_pulse_actions` is a package somewhere on sys.path that may look like this:

```
my_pulse_actions/
  __init__.py
  my_action_pulseaction.py
  my_action.pulseaction.yaml
  some_folder/
    my_otheraction_pulseaction.py
    my_otheraction.pulseaction.yaml
```

Note that sub folders don't need to be python packages (there's no `some_folder/__init__.py`). Each `*_pulseaction.py`
module is found and imported individually, the package is just used to locate the directory.

## Roadmap

You can track development on Pulse [here](https://bohdon.notion.site/f656af523ead43a5893679d13e36e6aa).
