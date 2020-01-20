
import pymel.core as pm

import pulse


class DisplayLayerAction(pulse.BuildAction):

    def validate(self):
        if not len(self.name):
            raise pulse.BuildActionError('name cannot be empty')

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
