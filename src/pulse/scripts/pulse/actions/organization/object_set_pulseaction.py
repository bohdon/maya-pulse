import pymel.core as pm

from pulse.core.buildItems import BuildAction, BuildActionError


class ObjectSetAction(BuildAction):

    def validate(self):
        if not len(self.name):
            raise BuildActionError('name cannot be empty')

    def run(self):
        objectSet = pm.ls(self.name)
        if len(objectSet) and isinstance(objectSet[0], pm.nt.ObjectSet):
            objectSet = objectSet[0]
        else:
            objectSet = pm.sets(n=self.name, empty=True)

        objectSet.addMembers(self.objects)
