import pymel.core as pm

from pulse.buildItems import BuildAction, BuildActionError
from pulse.buildItems import BuildActionAttributeType as AttrType


class DisplayLayerAction(BuildAction):
    id = 'Pulse.DisplayLayer'
    display_name = 'Display Layer'
    description = 'Create a display layer'
    category = 'Organization'
    attr_definitions = [
        dict(name='name', type=AttrType.STRING, description='The name of the display layer'),
        dict(name='objects', type=AttrType.NODE_LIST, description='List of objects to add to the display layer'),
        dict(name='displayType', type=AttrType.OPTION, options=['Normal', 'Template', 'Reference'], value=0,
             description='The display mode to set on the layer'),
        dict(name='visible', type=AttrType.BOOL, value=True),
        dict(name='shading', type=AttrType.BOOL, value=True),
        dict(name='texturing', type=AttrType.BOOL, value=True),
        dict(name='playback', type=AttrType.BOOL, value=True),
    ]

    def validate(self):
        if not len(self.name):
            raise BuildActionError('name cannot be empty')

    def run(self):
        layer = pm.ls(self.name)
        if len(layer) and isinstance(layer[0], pm.nt.DisplayLayer):
            pm.editDisplayLayerMembers(layer[0], self.objects)
            layer = layer[0]
        else:
            layer = pm.createDisplayLayer(self.objects, n=self.name)
        layer.visibility.set(self.visible)
        layer.displayType.set(self.displayType)
        layer.shading.set(self.shading)
        layer.texturing.set(self.texturing)
        layer.playback.set(self.playback)
