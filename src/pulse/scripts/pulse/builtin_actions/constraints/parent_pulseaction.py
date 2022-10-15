from pulse.buildItems import BuildAction, BuildActionError


class ParentAction(BuildAction):

    def validate(self):
        if not self.parent:
            raise BuildActionError("parent must be set")
        if not self.child:
            raise BuildActionError("child must be set")

    def run(self):
        self.child.setParent(self.parent)
