
import sys
import maya.api.OpenMaya as om

import pulse.views
import pulse.core

# the list of all cmd classes in this plugin
CMD_CLASSES = []


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


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

    def isUndoable(self):
        return True

    def getBlueprintModel(self):
        model = pulse.views.BlueprintUIModel.getDefaultModel()
        print('debug: plugin using BlueprintUIModel: ', model)
        return model

    def toStrData(self, data):
        return pulse.core.serializeAttrValue(data)

    def fromStrData(self, data):
        return pulse.core.deserializeAttrValue(data)


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
        print(self.__class__.__name__, args)
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        if len(args) != 2:
            raise TypeError(
                "pulseSetActionAttr() takes exactly 2 arguments "
                "({0} given)".format(len(args)))

        try:
            argparser = om.MArgParser(self.syntax(), args)
        except RuntimeError:
            om.MGlobal.displayError('Error while parsing arguments')
            raise

        # attr path
        self.attrPath = argparser.commandArgumentString(0)

        # attr value
        self.newStrValue = argparser.commandArgumentString(1)

        # variant index
        self.variantIndex = -1
        if argparser.isFlagSet(PulseSetActionAttrCmd.variantFlag.flag):
            self.variantIndex = argparser.flagArgumentInt(
                PulseSetActionAttrCmd.variantFlag.flag, 0)

    def redoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            # store old value as str
            self.oldStrValue = self.toStrData(
                blueprintModel.getActionAttr(
                    self.attrPath, self.variantIndex))

            # deserialize str value into objects
            value = self.fromStrData(self.newStrValue)
            blueprintModel.setActionAttr(
                self.attrPath, value, self.variantIndex)

    def undoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            # deserialize str value into objects
            value = self.fromStrData(self.oldStrValue)
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
        print(self.__class__.__name__, args)
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        if len(args) != 2:
            raise TypeError(
                "pulseSetIsVariantAttr() takes exactly 2 arguments "
                "({0} given)".format(len(args)))

        try:
            argparser = om.MArgParser(self.syntax(), args)
        except RuntimeError:
            om.MGlobal.displayError('Error while parsing arguments')
            raise

        # attr path
        self.attrPath = argparser.commandArgumentString(0)

        # is variant value
        self.newValue = argparser.commandArgumentBool(1)

    def redoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            # TODO: fail if not changing anything

            # snapshot the whole action proxy, since it may change
            # significantly when modifying variant attrs
            self.oldStrData = self.toStrData(
                blueprintModel.getActionDataForAttrPath(
                    self.attrPath))
            blueprintModel.setIsActionAttrVariant(
                self.attrPath, self.newValue)

    def undoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            oldData = self.fromStrData(self.oldStrData)
            blueprintModel.setActionDataForAttrPath(
                self.attrPath, oldData)


CMD_CLASSES.append(PulseSetIsVariantAttrCmd)


class PulseMoveStepCmd(PulseCmdBase):
    """
    Command to move or rename a Pulse BuildStep.
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
        print(self.__class__.__name__, args)
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


class PulseDeleteStepCmd(PulseCmdBase):
    """
    Command to delete a Pulse BuildStep.
    """

    cmdName = "pulseDeleteStep"

    pathFlagType = om.MSyntax.kString

    @staticmethod
    def createCmd():
        return PulseDeleteStepCmd()

    @staticmethod
    def createSyntax():
        syntax = om.MSyntax()
        syntax.addArg(PulseDeleteStepCmd.pathFlagType)
        return syntax

    def doIt(self, args):
        print(self.__class__.__name__, args)
        self.parseArguments(args)
        self.redoIt()

    def parseArguments(self, args):
        if len(args) != 1:
            raise TypeError(
                "pulseMoveStep() takes exactly 1 argument "
                "({0} given)".format(len(args)))

        try:
            argdb = om.MArgDatabase(self.syntax(), args)
        except RuntimeError:
            om.MGlobal.displayError('Error while parsing arguments')
            raise

        self.stepPath = argdb.commandArgumentString(0)

    def redoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel:
            # save the serialized step data before deleting
            self.deletedContent = blueprintModel.getStepData(self.stepPath)
            if not blueprintModel.deleteStep(self.stepPath):
                raise RuntimeError("Failed to delete BuildStep")

    def undoIt(self):
        blueprintModel = self.getBlueprintModel()
        if blueprintModel and self.deletedContent:
            blueprintModel.createStep(self.stepPath, self.deletedContent)


CMD_CLASSES.append(PulseDeleteStepCmd)


def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    for cmd in CMD_CLASSES:
        pluginFn.registerCommand(cmd.cmdName, cmd.createCmd, cmd.createSyntax)


def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    for cmd in CMD_CLASSES:
        pluginFn.deregisterCommand(cmd.cmdName)
