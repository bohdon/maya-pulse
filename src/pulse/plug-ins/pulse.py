import os

import maya.api.OpenMaya as om

from pulse.serializer import serializeAttrValue, deserializeAttrValue
from pulse.ui.core import BlueprintUIModel

# the list of all cmd classes in this plugin
CMD_CLASSES = []


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


def getBlueprintModel():
    model = BlueprintUIModel.getDefaultModel()
    return model


class CmdFlag(object):
    """
    Simple class for wrapping arguments needed to build
    a maya command Flag. Can be unpacked and passed to
    MSyntax.addFlag()
    """

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
    """
    Base class for any Pulse command, provides some
    basic argument parsing and data serialization utils.
    """

    cmdName = None
    # required number of arguments
    numArgs = 0

    def isUndoable(self):
        return True

    def getArgParser(self, args):
        if len(args) != self.numArgs:
            raise TypeError(
                "{0.cmdName}() takes exactly {0.numArgs} arguments "
                "({1} given)".format(self, len(args)))

        try:
            argparser = om.MArgParser(self.syntax(), args)
        except RuntimeError:
            om.MGlobal.displayError('Error while parsing arguments')
            raise

        return argparser


class PulseCreateStepCmd(PulseCmdBase):
    """
    Command to create a Pulse BuildStep.
    """

    cmdName = "pulseCreateStep"

    pathFlagType = om.MSyntax.kString
    indexFlagType = om.MSyntax.kLong
    dataFlagType = om.MSyntax.kString
    numArgs = 3

    @staticmethod
    def createCmd():
        return PulseCreateStepCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addArg(PulseCreateStepCmd.pathFlagType)
        syntax.addArg(PulseCreateStepCmd.indexFlagType)
        syntax.addArg(PulseCreateStepCmd.dataFlagType)
        return syntax

    def doIt(self, args):
        self.parseArguments(args)
        return self.redoIt()

    def parseArguments(self, args):
        argparser = self.getArgParser(args)
        self.stepPath = argparser.commandArgumentString(0)
        self.stepChildIndex = argparser.commandArgumentInt(1)
        self.stepStrData = argparser.commandArgumentString(2)

    def redoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            stepData = deserializeAttrValue(self.stepStrData)
            newStep = blueprintModel.createStep(self.stepPath, self.stepChildIndex, stepData)
            if not newStep:
                raise RuntimeError("Failed to create BuildStep")
            self.newStepPath = newStep.get_full_path()
            self.clearResult()
            self.setResult(self.newStepPath)

    def undoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel and self.newStepPath:
            blueprintModel.deleteStep(self.newStepPath)


CMD_CLASSES.append(PulseCreateStepCmd)


class PulseDeleteStepCmd(PulseCmdBase):
    """
    Command to delete a Pulse BuildStep.
    """

    cmdName = "pulseDeleteStep"

    pathFlagType = om.MSyntax.kString
    numArgs = 1

    @staticmethod
    def createCmd():
        return PulseDeleteStepCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addArg(PulseDeleteStepCmd.pathFlagType)
        return syntax

    def doIt(self, args):
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        argparser = self.getArgParser(args)
        self.stepPath = argparser.commandArgumentString(0)

    def redoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            # save the serialized step data before deleting
            step = blueprintModel.getStep(self.stepPath)
            if not step:
                raise RuntimeError(
                    "BuildStep not found: {0}".format(self.stepPath))
            self.deletedStrData = serializeAttrValue(step.serialize())
            self.deletedChildIndex = step.index_in_parent()
            if not blueprintModel.deleteStep(self.stepPath):
                raise RuntimeError("Failed to delete BuildStep")

    def undoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel and self.deletedStrData:
            deletedData = deserializeAttrValue(self.deletedStrData)
            parentPath = os.path.dirname(self.stepPath)
            blueprintModel.createStep(
                parentPath, self.deletedChildIndex, deletedData)


CMD_CLASSES.append(PulseDeleteStepCmd)


class PulseMoveStepCmd(PulseCmdBase):
    """
    Command to move or rename a Pulse BuildStep.
    """

    cmdName = "pulseMoveStep"

    sourceFlagType = om.MSyntax.kString
    targetFlagType = om.MSyntax.kString
    numArgs = 2

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
        argparser = self.getArgParser(args)
        self.sourcePath = argparser.commandArgumentString(0)
        self.targetPath = argparser.commandArgumentString(1)

    def redoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            # save the resolved path after performing the move
            self.resolvedTargetPath = blueprintModel.moveStep(
                self.sourcePath, self.targetPath)
            if self.resolvedTargetPath is None:
                raise RuntimeError("Failed to move BuildStep")

    def undoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            blueprintModel.moveStep(
                self.resolvedTargetPath, self.sourcePath)


CMD_CLASSES.append(PulseMoveStepCmd)


class PulseRenameStepCmd(PulseCmdBase):
    """
    Command to move or rename a Pulse BuildStep.
    """

    cmdName = "pulseRenameStep"

    pathFlagType = om.MSyntax.kString
    nameFlagType = om.MSyntax.kString
    numArgs = 2

    @staticmethod
    def createCmd():
        return PulseRenameStepCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addArg(PulseRenameStepCmd.pathFlagType)
        syntax.addArg(PulseRenameStepCmd.nameFlagType)
        return syntax

    def doIt(self, args):
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        argparser = self.getArgParser(args)
        self.stepPath = argparser.commandArgumentString(0)
        self.targetName = argparser.commandArgumentString(1)

    def redoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            # save the resolved path after performing the move
            step = blueprintModel.getStep(self.stepPath)
            self.oldName = step.name if step else ''
            self.resolvedTargetPath = blueprintModel.renameStep(
                self.stepPath, self.targetName)
            if self.resolvedTargetPath is None:
                raise RuntimeError("Failed to rename BuildStep")

    def undoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            blueprintModel.renameStep(
                self.resolvedTargetPath, self.oldName)


CMD_CLASSES.append(PulseRenameStepCmd)


class PulseSetActionAttrCmd(PulseCmdBase):
    """
    Command to modify the value of a Pulse BuildAction attribute.
    """

    cmdName = "pulseSetActionAttr"

    # the full path to the attribute, e.g. 'My/Build/Step.myAttr'
    attrPathArgType = om.MSyntax.kString
    # the serialized value of the attribute, e.g. '123'
    valueArgType = om.MSyntax.kString
    # the index of the variant to modify
    variantFlag = CmdFlag('-v', '-variant', om.MSyntax.kLong)
    numArgs = 2

    @staticmethod
    def createCmd():
        return PulseSetActionAttrCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addArg(PulseSetActionAttrCmd.attrPathArgType)
        syntax.addArg(PulseSetActionAttrCmd.valueArgType)
        syntax.addFlag(*PulseSetActionAttrCmd.variantFlag)
        return syntax

    def doIt(self, args):
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        argparser = self.getArgParser(args)
        self.attrPath = argparser.commandArgumentString(0)
        self.newStrValue = argparser.commandArgumentString(1)
        self.variantIndex = -1
        if argparser.isFlagSet(PulseSetActionAttrCmd.variantFlag.flag):
            self.variantIndex = argparser.flagArgumentInt(
                PulseSetActionAttrCmd.variantFlag.flag, 0)

    def redoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            # store old value as str
            self.oldStrValue = serializeAttrValue(
                blueprintModel.getActionAttr(
                    self.attrPath, self.variantIndex))

            # deserialize str value into objects
            value = deserializeAttrValue(self.newStrValue)
            blueprintModel.setActionAttr(
                self.attrPath, value, self.variantIndex)

    def undoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            # deserialize str value into objects
            value = deserializeAttrValue(self.oldStrValue)
            blueprintModel.setActionAttr(
                self.attrPath, value, self.variantIndex)


CMD_CLASSES.append(PulseSetActionAttrCmd)


class PulseSetIsVariantAttrCmd(PulseCmdBase):
    """
    Command to change an attribute of a Pulse BuildAction attribute
    from being constant or variant.
    """

    cmdName = "pulseSetIsVariantAttr"

    # the full path to the attribute, e.g. 'My/Build/Step.myAttr'
    attrPathArgType = om.MSyntax.kString
    # whether the attribute should be variant
    valueArgType = om.MSyntax.kBoolean
    numArgs = 2

    @staticmethod
    def createCmd():
        return PulseSetIsVariantAttrCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addArg(PulseSetIsVariantAttrCmd.attrPathArgType)
        syntax.addArg(PulseSetIsVariantAttrCmd.valueArgType)
        return syntax

    def doIt(self, args):
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        argparser = self.getArgParser(args)
        self.attrPath = argparser.commandArgumentString(0)
        self.stepPath = self.attrPath.split('.')[0]
        self.newValue = argparser.commandArgumentBool(1)

    def redoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            # TODO: fail if not changing anything

            # snapshot the whole action proxy, since it may change
            # significantly when modifying variant attrs
            self.oldStrData = serializeAttrValue(
                blueprintModel.getActionData(
                    self.stepPath))
            blueprintModel.setIsActionAttrVariant(
                self.attrPath, self.newValue)

    def undoIt(self):
        blueprintModel = getBlueprintModel()
        if blueprintModel:
            oldData = deserializeAttrValue(self.oldStrData)
            blueprintModel.setActionData(
                self.stepPath, oldData)


CMD_CLASSES.append(PulseSetIsVariantAttrCmd)


def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    for cmd in CMD_CLASSES:
        pluginFn.registerCommand(cmd.cmdName, cmd.createCmd, cmd.createSyntax)


def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    for cmd in CMD_CLASSES:
        pluginFn.deregisterCommand(cmd.cmdName)
