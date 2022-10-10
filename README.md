# Pulse

A rigging framework and toolkit built for Maya.

## Development Testing

Pulse is still in early development, but if you want to try it out here's the entry point commands I am currently using:

```python
# toggle the Pulse UI
import pulse.ui

pulse.ui.toggleEditorUI()
```

```python
# development reload Pulse
import pymel.core as pm

try:
    import pulse.ui

    pulse.ui.tearDownUI()
except:
    pass

# keep track of the current scene
scene_name = pm.sceneName()

pm.newFile(force=True)
pm.unloadPlugin('pulse')

try:
    pulse.ui.destroyUIModelInstances()
except:
    pass

import pulse.vendor.mayacoretools as tools

tools.deleteModules('pulse*')

import pulse.ui

pulse.ui.showEditorUI()

# re-open last scene
if scene_name:
    pm.openFile(scene_name)
```

## Roadmap

You can track development on Pulse [here](https://bohdon.notion.site/f656af523ead43a5893679d13e36e6aa).
