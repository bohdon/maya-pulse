import os
from typing import List, Type

from maya.api.OpenMaya import MFnPlugin, MSyntax

from pulse.plugins import PulseCmdBase, CmdArg, CmdFlag
from pulse.core import serialize_attr_value, deserialize_attr_value

# the list of all cmd classes in this plugin
_CMD_CLASSES: List[Type[PulseCmdBase]] = []


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


def initializePlugin(plugin):
    plugin_fn = MFnPlugin(plugin)
    cmd_cls: Type[PulseCmdBase]
    for cmd_cls in _CMD_CLASSES:
        plugin_fn.registerCommand(cmd_cls.get_name(), cmd_cls.create_cmd, cmd_cls.create_syntax)


def uninitializePlugin(plugin):
    plugin_fn = MFnPlugin(plugin)
    cmd_cls: Type[PulseCmdBase]
    for cmd_cls in _CMD_CLASSES:
        plugin_fn.deregisterCommand(cmd_cls.get_name())


class PulseCreateStepCmd(PulseCmdBase):
    """
    Command to create a Pulse BuildStep.
    """

    step_path_arg = CmdArg(MSyntax.kString)
    child_index_arg = CmdArg(MSyntax.kLong)
    str_data_arg = CmdArg(MSyntax.kString)

    @classmethod
    def get_args(cls) -> List[CmdArg]:
        return [cls.step_path_arg, cls.child_index_arg, cls.str_data_arg]

    def parse_arguments(self, args):
        parser = self.get_arg_parser(args)
        self.step_path: str = self.get_arg(self.step_path_arg, parser)
        self.child_index: int = self.get_arg(self.child_index_arg, parser)
        self.str_data: str = self.get_arg(self.str_data_arg, parser)

    def doIt(self, args):
        self.parse_arguments(args)
        return self.redoIt()

    def redoIt(self):
        if self.blueprint_model:
            step_data = deserialize_attr_value(self.str_data)
            new_step = self.blueprint_model.create_step(self.step_path, self.child_index, step_data)
            if not new_step:
                raise RuntimeError("Failed to create BuildStep")
            self.new_step_path = new_step.get_full_path()
            self.clearResult()
            self.setResult(self.new_step_path)

    def undoIt(self):
        if self.blueprint_model and self.new_step_path:
            self.blueprint_model.delete_step(self.new_step_path)


_CMD_CLASSES.append(PulseCreateStepCmd)


class PulseDeleteStepCmd(PulseCmdBase):
    """
    Command to delete a Pulse BuildStep.
    """

    step_path_arg = CmdArg(MSyntax.kString)

    @classmethod
    def get_args(cls) -> List[CmdArg]:
        return [cls.step_path_arg]

    def parse_arguments(self, args):
        parser = self.get_arg_parser(args)
        self.step_path = self.get_arg(self.step_path_arg, parser)

    def doIt(self, args):
        self.parse_arguments(args)
        self.redoIt()

    def redoIt(self):
        # save the serialized step data before deleting
        step = self.blueprint_model.get_step(self.step_path)
        if not step:
            raise RuntimeError("BuildStep not found: {0}".format(self.step_path))
        self.deleted_str_data = serialize_attr_value(step.serialize())
        self.deleted_child_index = step.index_in_parent()
        if not self.blueprint_model.delete_step(self.step_path):
            raise RuntimeError("Failed to delete BuildStep")

    def undoIt(self):
        if self.deleted_str_data:
            deleted_data = deserialize_attr_value(self.deleted_str_data)
            parent_path = os.path.dirname(self.step_path)
            self.blueprint_model.create_step(parent_path, self.deleted_child_index, deleted_data)


_CMD_CLASSES.append(PulseDeleteStepCmd)


class PulseMoveStepCmd(PulseCmdBase):
    """
    Command to move or rename a Pulse BuildStep.
    """

    source_path_arg = CmdArg(MSyntax.kString)
    target_path_arg = CmdArg(MSyntax.kString)

    @classmethod
    def get_args(cls) -> List[CmdArg]:
        return [cls.source_path_arg, cls.target_path_arg]

    def parse_arguments(self, args):
        parser = self.get_arg_parser(args)
        self.source_path: str = self.get_arg(self.source_path_arg, parser)
        self.target_path: str = self.get_arg(self.target_path_arg, parser)

    def doIt(self, args):
        self.parse_arguments(args)
        self.redoIt()

    def redoIt(self):
        # save the resolved path after performing the move
        self.resolved_target_path = self.blueprint_model.move_step(self.source_path, self.target_path)
        if self.resolved_target_path is None:
            raise RuntimeError("Failed to move BuildStep")

    def undoIt(self):
        self.blueprint_model.move_step(self.resolved_target_path, self.source_path)


_CMD_CLASSES.append(PulseMoveStepCmd)


class PulseRenameStepCmd(PulseCmdBase):
    """
    Command to move or rename a Pulse BuildStep.
    """

    step_path_arg = CmdArg(MSyntax.kString)
    new_name_arg = CmdArg(MSyntax.kString)

    @classmethod
    def get_args(cls) -> List[CmdArg]:
        return [cls.step_path_arg, cls.new_name_arg]

    def parse_arguments(self, args):
        parser = self.get_arg_parser(args)
        self.step_path: str = self.get_arg(self.step_path_arg, parser)
        self.new_name: str = self.get_arg(self.new_name_arg, parser)

    def doIt(self, args):
        self.parse_arguments(args)
        self.redoIt()

    def redoIt(self):
        # save the resolved path after performing the move
        step = self.blueprint_model.get_step(self.step_path)
        self.old_name = step.name if step else ""
        self.resolved_target_path = self.blueprint_model.rename_step(self.step_path, self.new_name)
        if self.resolved_target_path is None:
            raise RuntimeError("Failed to rename BuildStep")

    def undoIt(self):
        self.blueprint_model.rename_step(self.resolved_target_path, self.old_name)


_CMD_CLASSES.append(PulseRenameStepCmd)


class PulseSetActionAttrCmd(PulseCmdBase):
    """
    Command to modify the value of a Pulse BuildAction attribute.
    """

    # the full path to the attribute, e.g. 'My/Build/Step.myAttr'
    attr_path_arg = CmdArg(MSyntax.kString)
    # the serialized value of the attribute, e.g. '123'
    new_value_arg = CmdArg(MSyntax.kString)
    # the index of the variant to modify
    variant_index_flag = CmdFlag("-v", "-variant", MSyntax.kLong, -1)

    @classmethod
    def get_args(cls) -> List[CmdArg]:
        return [cls.attr_path_arg, cls.new_value_arg]

    @classmethod
    def get_flags(cls) -> List[CmdFlag]:
        return [cls.variant_index_flag]

    def parse_arguments(self, args):
        parser = self.get_arg_parser(args)
        self.attr_path: str = self.get_arg(self.attr_path_arg, parser)
        self.new_value: str = self.get_arg(self.new_value_arg, parser)
        self.variant_index: int = self.get_flag(self.variant_index_flag, parser)

    def doIt(self, args):
        self.parse_arguments(args)
        self.redoIt()

    def redoIt(self):
        # store old value as str
        self.old_str_value = serialize_attr_value(
            self.blueprint_model.get_action_attr(self.attr_path, self.variant_index)
        )

        # deserialize str value into objects
        value = deserialize_attr_value(self.new_value)
        self.blueprint_model.set_action_attr(self.attr_path, value, self.variant_index)

    def undoIt(self):
        # deserialize str value into objects
        value = deserialize_attr_value(self.old_str_value)
        self.blueprint_model.set_action_attr(self.attr_path, value, self.variant_index)


_CMD_CLASSES.append(PulseSetActionAttrCmd)


class PulseSetIsVariantAttrCmd(PulseCmdBase):
    """
    Command to change an attribute of a Pulse BuildAction attribute
    from being constant or variant.
    """

    # the full path to the attribute, e.g. 'My/Build/Step.myAttr'
    attr_path_arg = CmdArg(MSyntax.kString)
    # whether the attribute should be variant
    new_value_arg = CmdArg(MSyntax.kBoolean)

    @classmethod
    def get_args(cls) -> List[CmdArg]:
        return [cls.attr_path_arg, cls.new_value_arg]

    def parse_arguments(self, args):
        parser = self.get_arg_parser(args)
        self.attr_path: str = self.get_arg(self.attr_path_arg, parser)
        self.new_value: bool = self.get_arg(self.new_value_arg, parser)
        self.step_path: str = self.attr_path.split(".")[0]

    def doIt(self, args):
        self.parse_arguments(args)
        self.redoIt()

    def redoIt(self):
        # TODO: fail if not changing anything

        # snapshot the whole action proxy, since it may change
        # significantly when modifying variant attrs
        self.old_str_data = serialize_attr_value(self.blueprint_model.get_action_data(self.step_path))
        self.blueprint_model.set_is_action_attr_variant(self.attr_path, self.new_value)

    def undoIt(self):
        old_data = deserialize_attr_value(self.old_str_data)
        self.blueprint_model.set_action_data(self.step_path, old_data)


_CMD_CLASSES.append(PulseSetIsVariantAttrCmd)


class PulseSetIsActionMirroredCmd(PulseCmdBase):
    """
    Command to change whether a Pulse BuildAction is mirrored or not.
    """

    # the full path to the attribute, e.g. 'My/Build/Step.myAttr'
    attr_path_arg = CmdArg(MSyntax.kString)
    # whether the action should be mirrored
    new_value_arg = CmdArg(MSyntax.kBoolean)

    @classmethod
    def get_args(cls) -> List[CmdArg]:
        return [cls.attr_path_arg, cls.new_value_arg]

    def parse_arguments(self, args):
        parser = self.get_arg_parser(args)
        self.step_path: str = self.get_arg(self.attr_path_arg, parser)
        self.new_value: bool = self.get_arg(self.new_value_arg, parser)

    def doIt(self, args):
        self.parse_arguments(args)
        self.redoIt()

    def redoIt(self):
        # TODO: fail if not changing anything
        self.old_value = self.blueprint_model.is_action_mirrored(self.step_path)
        self.blueprint_model.set_is_action_mirrored(self.step_path, self.new_value)

    def undoIt(self):
        self.blueprint_model.set_is_action_attr_variant(self.step_path, self.old_value)


_CMD_CLASSES.append(PulseSetIsActionMirroredCmd)
