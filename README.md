# Pulse Rigging Framework for Maya

A rigging framework for Maya.


## Development Testing

Pulse is still in early development, but if you want to try it out here's the entry point commands I am currently using:

```python
# toggle the pulse UI
import pulse.views
pulse.views.togglePulseUI()
```

```python
# development reload the pulse package
try:
    import pulse.views
    pulse.views.hidePulseUI()
except:
    pass

import pulse.vendor.mayacoretools as tools
tools.deleteModules('pulse*')

import pulse.views
pulse.views.showPulseUI()
```

## Roadmap

You can view the Pulse roadmap on trello here:

[Pulse Roadmap](https://trello.com/b/x1EgkZA7)
