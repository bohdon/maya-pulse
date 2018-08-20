
import sys
import maya.api.OpenMaya as om

import pulse.views

# the list of all cmd classes in this plugin
CMD_CLASSES = []


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


class CmdArg(object):
    def __init__(self, argType=None):
        self.argType = argType

    def __iter__(self):
        if self.argType is not None:
            yield self.argType


class CmdFlag(object):
    def __init__(self, flag, flagLong, flagType=None):
        self.flag = flag
        self.flagLong = flagLong
        self.flagType = flagType

    def __iter__(self):
        yield self.flag
        yield self.flagLong
        if self.flagType is not None:
            yield self.flagType


class PulseCmdBase(om.MPxCommand):

    def getBlueprintModel(self):
        return pulse.views.BlueprintUIModel.getDefaultModel()

    def isUndoable(self):
        return True


class PulseSetActionAttrCmd(PulseCmdBase):
    """
    Command to modify the value of a Pulse BuildAction attribute.
    """

    cmdName = "pulseSetActionAttr"

    nameArgType = om.MSyntax.kString
    valueArgType = om.MSyntax.kString

    @staticmethod
    def createCmd():
        return PulseSetActionAttrCmd()

    @staticmethod
    def createSyntax():
        """
        Syntax docs go here
        """
        syntax = om.MSyntax()
        syntax.addArg(PulseSetActionAttrCmd.nameArgType)
        syntax.addArg(PulseSetActionAttrCmd.valueArgType)
        return syntax

    def doIt(self, args):
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        if len(args) != 2:
            raise TypeError(
                "pulseMoveStep() takes exactly 2 arguments "
                "({0} given)".format(len(args)))

        try:
            argparser = om.MArgParser(self.syntax(), args)
        except RuntimeError:
            om.MGlobal.displayError('Error while parsing arguments')
            raise

        self.attrName = argparser.commandArgumentString(0)
        self.newValue = argparser.commandArgumentString(1)
        self.oldValue = "old value"

        # TODO: rerieve old value
        # self.oldValue = 1
        # print(PulseSetActionAttrCmd.valueFlag.flag)

        print(self.attrName, self.newValue)

    def redoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            blueprintModel.setBlueprintAttr(self.attrName, self.newValue)

    def undoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            blueprintModel.setBlueprintAttr(self.attrName, self.oldValue)


CMD_CLASSES.append(PulseSetActionAttrCmd)


class PulseMoveStepCmd(PulseCmdBase):
    """
    Command to rename a Pulse BuildStep.
    """

    cmdName = "pulseMoveStep"

    sourceFlagType = om.MSyntax.kString
    targetFlagType = om.MSyntax.kString

    @staticmethod
    def createCmd():
        return PulseMoveStepCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addArg(PulseMoveStepCmd.sourceFlagType)
        syntax.addArg(PulseMoveStepCmd.targetFlagType)
        return syntax

    def doIt(self, args):
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        if len(args) != 2:
            raise TypeError(
                "pulseMoveStep() takes exactly 2 arguments "
                "({0} given)".format(len(args)))

        try:
            argdb = om.MArgDatabase(self.syntax(), args)
        except RuntimeError:
            om.MGlobal.displayError('Error while parsing arguments')
            raise

        self.sourcePath = argdb.commandArgumentString(0)
        self.targetPath = argdb.commandArgumentString(1)

    def redoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            # save the resolved path after performing the move
            self.resolvedTargetPath = blueprintModel.moveStep(
                self.sourcePath, self.targetPath)
            if self.resolvedTargetPath is None:
                raise RuntimeError("Failed to move BuildStep")

    def undoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            blueprintModel.moveStep(
                self.resolvedTargetPath, self.sourcePath)


CMD_CLASSES.append(PulseMoveStepCmd)


def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    for cmd in CMD_CLASSES:
        pluginFn.registerCommand(cmd.cmdName, cmd.createCmd, cmd.createSyntax)


def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    for cmd in CMD_CLASSES:
        pluginFn.deregisterCommand(cmd.cmdName)
