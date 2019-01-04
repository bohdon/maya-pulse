# Pulse Rigging Framework for Maya

A rigging framework for Maya.


## Development Testing

Pulse is still in early development, but if you want to try it out here's the entry point commands I am currently using:

```python
# toggle the Pulse UI
import pulse.views
pulse.views.toggleEditorUI()
```

```python
# development reload Pulse
try:
    pulse.views.tearDownUI()
except:
    pass

import pymel.core as pm
pm.newFile(force=True)
pm.unloadPlugin('pulse')

try:
    pulse.views.destroyUIModelInstances()
except:
    pass

import pulse.vendor.mayacoretools as tools
tools.deleteModules('pulse*')

import pulse.views
pulse.views.showEditorUI()
```

## Roadmap

You can view the Pulse roadmap on trello here:

[Pulse Roadmap](https://trello.com/b/x1EgkZA7)
