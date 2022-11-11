"""
Utils for authoring Maya python plug-ins.
"""
from typing import List, Optional

from maya.api.OpenMaya import MSyntax, MArgParser, MGlobal, MPxCommand

from .ui.core import BlueprintUIModel


class CmdSyntaxItem(object):
    """
    Base class for an argument or flag that can be added to an MSyntax.
    """

    def __init__(self):
        # the value of this item
        self.value = None

    def add_to(self, syntax: MSyntax):
        """
        Add this item to an MSyntax.
        """
        raise NotImplementedError

    def get_value(self, arg_parser: MArgParser, index: int):
        """
        Return the value of this item from an arg parser.
        """
        raise NotImplementedError


class CmdArg(CmdSyntaxItem):
    """
    Simple class for wrapping argument types for a maya command.
    Designed to pass the `arg_type` to MSyntax.addArg().
    """

    def __init__(self, arg_type: int):
        super().__init__()
        self.arg_type = arg_type

    def add_to(self, syntax: MSyntax):
        syntax.addArg(self.arg_type)

    def get_value(self, arg_parser: MArgParser, index: int):
        if self.arg_type == MSyntax.kBoolean:
            return arg_parser.commandArgumentBool(index)
        elif self.arg_type == MSyntax.kDouble:
            return arg_parser.commandArgumentDouble(index)
        elif self.arg_type == MSyntax.kLong:
            return arg_parser.commandArgumentInt(index)
        elif self.arg_type == MSyntax.kAngle:
            return arg_parser.commandArgumentMAngle(index)
        elif self.arg_type == MSyntax.kDistance:
            return arg_parser.commandArgumentMDistance(index)
        elif self.arg_type == MSyntax.kTime:
            return arg_parser.commandArgumentMTime(index)
        elif self.arg_type == MSyntax.kString:
            return arg_parser.commandArgumentString(index)


class CmdFlag(CmdSyntaxItem):
    """
    Simple class for wrapping arguments needed to build a maya command Flag.
    Can be unpacked and passed to MSyntax.addFlag().
    """

    def __init__(self, flag: str, flag_long: str, flag_type: Optional[int] = None, default=None):
        super().__init__()
        self.flag = flag
        self.flag_long = flag_long
        self.flag_type = flag_type
        self.default = default

    def add_to(self, syntax: MSyntax):
        args = [self.flag, self.flag_long]
        if self.flag_type is not None:
            args.append(self.flag_type)
        syntax.addFlag(*args)

    def get_value(self, arg_parser: MArgParser, index: int):
        if not arg_parser.isFlagSet(self.flag):
            return self.default
        if self.flag_type == MSyntax.kBoolean:
            return arg_parser.flagArgumentBool(self.flag, index)
        elif self.flag_type == MSyntax.kDouble:
            return arg_parser.flagArgumentDouble(self.flag, index)
        elif self.flag_type == MSyntax.kLong:
            return arg_parser.flagArgumentInt(self.flag, index)
        elif self.flag_type == MSyntax.kAngle:
            return arg_parser.flagArgumentMAngle(self.flag, index)
        elif self.flag_type == MSyntax.kDistance:
            return arg_parser.flagArgumentMDistance(self.flag, index)
        elif self.flag_type == MSyntax.kTime:
            return arg_parser.flagArgumentMTime(self.flag, index)
        elif self.flag_type == MSyntax.kString:
            return arg_parser.flagArgumentString(self.flag, index)


class PulseCmdBase(MPxCommand):
    """
    Base class for any Pulse command, provides argument parsing utils to simplify writing commands.
    """

    @classmethod
    def create_cmd(cls):
        """
        Create and return a new instance of this command.
        """
        return cls()

    @classmethod
    def create_syntax(cls):
        """
        Return an MSyntax for the command.
        """
        syntax = MSyntax()
        for arg in cls.get_args():
            arg.add_to(syntax)
        for flag in cls.get_flags():
            flag.add_to(syntax)
        return syntax

    @classmethod
    def get_name(cls):
        """
        Return the name of the command.
        """
        # take class name, strip Cmd suffix, and make first letter lowercase
        # 'PulseMyActionCmd' -> 'pulseMyAction'
        return cls.__name__[0].lower() + cls.__name__[1:-3]

    @classmethod
    def get_args(cls) -> List[CmdArg]:
        """
        Return all available arguments.
        """
        return []

    @classmethod
    def get_flags(cls) -> List[CmdFlag]:
        """
        Return all available flags.
        """
        return []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arg_parser = None

    def get_arg_parser(self, args):
        """
        Return an MArgParser for the given args. Ensures that the number of arguments is valid.
        """
        num_args = len(self.get_args())
        if len(args) != num_args:
            raise TypeError(f"{self.get_name()}() takes exactly {num_args} arguments ({len(args)} given)")

        try:
            arg_parser = MArgParser(self.syntax(), args)
        except RuntimeError:
            MGlobal.displayError("Error while parsing arguments")
            raise

        return arg_parser

    def _get_arg_index(self, arg: CmdArg) -> int:
        args = self.get_args()
        try:
            return args.index(arg)
        except ValueError:
            return -1

    def get_arg(self, arg: CmdArg, arg_parser: MArgParser):
        """
        Return the value of an argument.
        """
        index = self._get_arg_index(arg)
        if index >= 0:
            return arg.get_value(arg_parser, index)

    def _get_flag_index(self, flag: CmdFlag) -> int:
        flags = self.get_flags()
        try:
            return flags.index(flag)
        except ValueError:
            return -1

    def get_flag(self, flag: CmdFlag, arg_parser: MArgParser):
        """
        Return the value of a flag.
        """
        index = self._get_flag_index(flag)
        if index >= 0:
            return flag.get_value(arg_parser, index)

    def parse_arguments(self, args):
        """
        Parse any arguments. Use `get_arg_parser`, `get_arg` and `get_flag` to easily access values.
        """
        pass

    def isUndoable(self):
        return True

    @property
    def blueprint_model(self) -> BlueprintUIModel:
        return BlueprintUIModel.get()
