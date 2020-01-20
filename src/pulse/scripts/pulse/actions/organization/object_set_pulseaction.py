
import pymel.core as pm

import pulse


class ObjectSetAction(pulse.BuildAction):

    def validate(self):
        if not len(self.name):
            raise pulse.BuildActionError('name cannot be empty')

    def run(self):
        objectSet = pm.ls(self.name)
        if len(objectSet) and isinstance(objectSet[0], pm.nt.ObjectSet):
            objectSet = objectSet[0]
        else:
            objectSet = pm.sets(n=self.name, empty=True)

        objectSet.addMembers(self.objects)
