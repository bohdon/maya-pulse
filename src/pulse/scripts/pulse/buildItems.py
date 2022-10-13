import logging
import os
import re
from typing import List, Iterable, Optional

import maya.cmds as cmds

from .vendor import pymetanode as meta
from .rigs import RIG_METACLASS
from .serializer import UnsortableOrderedDict

LOG = logging.getLogger(__name__)
LOG_LEVEL_KEY = 'PYLOG_%s' % LOG.name.split('.')[0].upper()
LOG.setLevel(os.environ.get(LOG_LEVEL_KEY, 'INFO').upper())

BUILD_ACTION_MAP = {}


def _increment_name(name: str) -> str:
    """
    Increment a name by adding or increasing a numerical suffix.
    """
    num_match = re.match('(.*?)([0-9]+$)', name)
    if num_match:
        base, num = num_match.groups()
        return base + str(int(num) + 1)
    else:
        return name + ' 1'


def _copy_data(data, ref_node=None):
    """
    Performs a deep copy of the given data using pymetanode to encode and decode the values.
    """
    return meta.decodeMetaData(meta.encodeMetaData(data), ref_node)


def get_registered_action(action_id) -> Optional[dict]:
    """
    Find a BuildAction config and class by action id

    Args:
        action_id (str): A BuildAction id

    Returns:
        A dict containing {'config':dict, 'class':class}
    """
    # TODO: use a class for the entry instead of just a specific layout dict
    if action_id in BUILD_ACTION_MAP:
        return BUILD_ACTION_MAP[action_id]


def get_build_action_config(action_id) -> Optional[dict]:
    """
    Return a BuildAction config by action id

    Args:
        action_id (str): A BuildAction id
    """
    action = get_registered_action(action_id)
    if action:
        return action['config']


def _get_build_action_config_for_class(action_cls: type['BuildAction']) -> Optional[dict]:
    """
    Return the config that is associated with a BuildAction class.
    Performs the search by looking for a matching class and returning
    its paired config, instead of looking for the config by id.

    Args:
        action_cls: A BuildAction class
    """
    for v in BUILD_ACTION_MAP.values():
        if v['class'] is action_cls:
            return v['config']


def get_build_action_class(action_id) -> type['BuildAction']:
    """
    Return a BuildAction class by action id

    Args:
        action_id (str): A BuildAction id
    """
    action = get_registered_action(action_id)
    if action:
        return action['class']


def get_registered_action_ids() -> Iterable[str]:
    """
    Return all the ids of registered BuildActions
    """
    return BUILD_ACTION_MAP.keys()


def get_registered_actions() -> dict[str, dict]:
    """
    Return all registered BuildAction configs and classes organized by their id

    Returns:
        A dict of {str: {'config': dict, 'class': BuildAction class}}
    """
    return {k: v for k, v in BUILD_ACTION_MAP.items()}


def get_registered_action_configs() -> List[dict]:
    """
    Return all registered BuildAction configs

    Returns:
        A dict of {str: {'config': dict, 'class': BuildAction class}}
    """
    return [i['config'] for i in BUILD_ACTION_MAP.values()]


def register_actions(action_config: dict, action_cls: type['BuildAction']):
    """
    Register one or more BuildAction classes

    Args:
        action_config: dict
            A config dict for a BuildAction.
        action_cls: BuildAction class
            A BuildAction class.
    """
    # TODO: prevent registration of invalid configs
    action = {
        'config': action_config,
        'class': action_cls,
    }
    action_id = action_config['id']
    if action_id in BUILD_ACTION_MAP:
        LOG.error("A BuildAction already exists with id: %s", action_id)
        return

    BUILD_ACTION_MAP[action_id] = action


def unregister_action(action_id):
    if action_id in BUILD_ACTION_MAP:
        del BUILD_ACTION_MAP[action_id]


class BuildActionError(Exception):
    """
    A BuildAction was misconfigured or failed during build
    """
    pass


class BuildActionData(object):
    """
    Contains attribute values for an action
    to be executed during a build step.
    """

    # TODO: add another base class with less cluttered namespace
    #       for use as the base of BuildActions

    def __init__(self, action_id=None):
        self._action_id = action_id
        self._config = None
        self._attr_values = {}
        # true if the action_id is set, but config data could not be found
        self._is_missing_config = False

        if self._action_id:
            self.find_action_config()

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.get_action_id()}'>"

    @property
    def config(self) -> dict:
        if self._config is not None:
            return self._config
        return {}

    def is_valid(self) -> bool:
        """
        Return True if there is a valid config data for this action
        """
        return self._config is not None

    def is_action_id_valid(self) -> bool:
        return self._action_id is not None

    def is_missing_config(self) -> bool:
        """
        Is there no config defined for the current action_id?
        """
        return self._is_missing_config

    def get_action_id(self) -> str:
        """
        Return the id of the BuildAction
        """
        return self._action_id

    def get_short_action_id(self) -> str:
        """
        Return the last part of the action's id, after any '.'
        """
        if self._action_id:
            return self._action_id.split('.')[-1]

    def find_action_config(self):
        """
        Get the config for the current action_id and store it on this data
        """
        self._config = get_build_action_config(self._action_id)
        if self._config is None:
            self._is_missing_config = True
            LOG.warning(f"Failed to find action config for %s", self._action_id)
        else:
            self._is_missing_config = False

    def num_attrs(self) -> int:
        """
        Return the number of attributes that this BuildAction has
        """
        return len(self.get_attrs())

    def get_attrs(self) -> List[dict]:
        """
        Return all attrs for this BuildAction class

        Returns:
            A list of dict representing all attr configs
        """
        if not self.is_valid():
            return []

        return self.config['attrs']

    def get_attr_names(self) -> Iterable[str]:
        """
        Return a list of attribute names for this BuildAction class
        """
        for attr in self.get_attrs():
            yield attr['name']

    def has_attr_config(self, attr_name) -> bool:
        """
        Return True if this action's config contains the attribute.
        """
        return self.get_attr_config(attr_name) is not None

    def has_attr(self, attr_name) -> bool:
        """
        Return True if this action data includes the attribute.
        This doesn't mean it has a value for the attribute, only
        that it can potentially.
        """
        return attr_name in self.get_attr_names()

    def get_attr_config(self, attr_name) -> Optional[dict]:
        """
        Return config data for an attribute

        Args:
            attr_name (str): The name of a BuildAction attribute
        """
        if not self.is_valid():
            return

        for attr in self.config['attrs']:
            if attr['name'] == attr_name:
                return attr

    def get_attr_default_value(self, attr: dict):
        """
        Return the default value for an attribute

        Args:
            attr (dict): A BuildAction attribute config object
        """
        if not self.is_valid():
            return

        if 'value' in attr:
            return attr['value']
        else:
            attr_type = attr['type']
            if 'list' in attr_type:
                return []
            elif attr_type == 'bool':
                return False
            elif attr_type in ['int', 'float']:
                return 0
            elif attr_type == 'string':
                return ''

    def has_attr_value(self, attr_name) -> bool:
        """
        Return True if this action data contains a non-default value
        for the attribute.

        Args:
            attr_name (str): The name of a BuildAction attribute
        """
        return attr_name in self._attr_values

    def get_attr_value(self, attr_name, default=None):
        """
        Return the value for an attribute, or default if its
        value is not overridden in this action data.
        Use `get_attr_value_or_default` to default to the config-default
        value for the attribute.

        Args:
            attr_name: str
                The name of a BuildAction attribute.
            default: Any
                The default value to return if the attribute is not set.
        """
        return self._attr_values.get(attr_name, default)

    def get_attr_value_or_default(self, attr_name):
        if attr_name in self._attr_values:
            return self._attr_values[attr_name]
        else:
            config = self.get_attr_config(attr_name)
            if config:
                return self.get_attr_default_value(config)
            else:
                LOG.warning(f"BuildActionData attribute not found: %s", attr_name)

    def set_attr_value(self, attr_name, value):
        if value is None:
            self.del_attr_value(attr_name)
        else:
            self._attr_values[attr_name] = value

    def del_attr_value(self, attr_name):
        if attr_name in self._attr_values:
            del self._attr_values[attr_name]

    def serialize(self):
        """
        Return this BuildActionData as a serialized dict object
        """
        data = UnsortableOrderedDict()
        data['id'] = self._action_id
        if self.is_valid():
            for attr in self.get_attrs():
                if self.has_attr_value(attr['name']):
                    data[attr['name']] = self._attr_values[attr['name']]
        return data

    def deserialize(self, data):
        """
        Set all values on this BuildActionData from data

        Args:
            data: A dict containing serialized data for this action
        """
        self._action_id = data['id']

        # update config
        if self._action_id:
            self.find_action_config()

        # load values for all action attrs
        if self.is_valid():
            for attr in self.get_attrs():
                if attr['name'] in data:
                    self._attr_values[attr['name']] = data[attr['name']]

        elif len(data) > 1:
            # if config didn't load, don't throw away the attribute values
            LOG.warning("Failed to find BuildAction config: %s, preserving serialized attr values", self._action_id)
            for k, v in data.items():
                self._attr_values[k] = v


class BuildActionDataVariant(BuildActionData):
    """
    Contains a partial set of attribute values.
    """

    # TODO: prevent setting an attribute that's not in the variant

    def __init__(self, action_id=None):
        super(BuildActionDataVariant, self).__init__(action_id=action_id)
        # names of all attributes that are in this variant
        self._variant_attrs: List[str] = []

    def get_variant_attrs(self) -> List[str]:
        """
        Return the list of all variant attribute names
        """
        return self._variant_attrs

    def get_attrs(self):
        """
        Return all attrs for this BuildAction class

        Returns:
            A list of dict representing all attr configs
        """
        if not self.is_valid():
            return []

        return [a for a in self.config['attrs'] if a['name'] in self.get_variant_attrs()]

    def is_variant_attr(self, attr_name):
        """
        Return True if the attribute is contained in this variant.
        This doesn't mean a non-default value is set for the attribute.

        Args:
            attr_name (str): The name of a BuildAction attribute
        """
        return attr_name in self.get_variant_attrs()

    def set_is_variant_attr(self, attr_name: str, is_variant: bool):
        """
        Set whether an attr is variant or not.

        Args:
            attr_name (str): The name of a BuildAction attribute
            is_variant (bool): Whether the attribute should be variant or not
        """
        if is_variant:
            self.add_variant_attr(attr_name)
        else:
            self.remove_variant_attr(attr_name)

    def add_variant_attr(self, attr_name: str):
        """
        Add an attribute to this variant.

        Args:
            attr_name (str): The name of a BuildAction attribute
        """
        if attr_name in self._variant_attrs:
            return

        if not self.has_attr_config(attr_name):
            return

        self._variant_attrs.append(attr_name)
        self._variant_attrs.sort()

    def remove_variant_attr(self, attr_name: str):
        """
        Remove an attribute from the list of variant attributes,
        copying the value from the first variant into the default set
        of attr values if applicable.

        Args:
            attr_name (str): The name of an action attribute
        """
        if attr_name not in self._variant_attrs:
            return

        self._variant_attrs.remove(attr_name)

        if self.has_attr_value(attr_name):
            self.del_attr_value(attr_name)

    def clear_variant_attrs(self):
        """
        Remove all variant attributes, copying the values
        from the first variant into the default set of attr values
        if applicable.
        """
        attr_names = self._variant_attrs[:]
        for attrName in attr_names:
            self.remove_variant_attr(attrName)

    def serialize(self):
        data = super(BuildActionDataVariant, self).serialize()
        data['variantAttrs'] = self._variant_attrs
        return data

    def deserialize(self, data):
        # must deserialize attrs first before attempting
        # to set values in super deserialize
        self._variant_attrs = data.get('variantAttrs', [])

        super(BuildActionDataVariant, self).deserialize(data)


class BuildActionProxy(BuildActionData):
    """
    Acts as a stand-in for a BuildAction during Blueprint editing.
    Contains all attribute values for the configured action, which
    are used to create real BuildActions at build time.

    The proxy can represent multiple BuildActions by adding 'variants'.
    This allows the user to create multiple actions where only the
    values that are unique per variant need to be set, and the
    remaining attributes will be the same on all actions.

    The proxy provides a method `action_iterator` which performs the
    actual construction of BuildActions for use at build time.
    """

    def __init__(self, action_id=None):
        super(BuildActionProxy, self).__init__(action_id=action_id)
        # names of all attributes that are unique per variant
        self._variantAttrs: List[str] = []
        # all BuildActionDataVariant instances in this proxy
        self._variants: List[BuildActionDataVariant] = []

    def get_editor_form_class(self):
        """
        Return the custom BuildActionProxyForm class to use for this action
        """
        return self.config.get('editorFormClassObj')

    def get_display_name(self):
        """
        Return the display name of the BuildAction.
        """
        return self.config.get('displayName', self.get_short_action_id())

    def get_color(self):
        """
        Return the color of this action when represented in the UI
        """
        if self.is_missing_config():
            return [0.8, 0, 0]
        else:
            return self.config.get('color', [1, 1, 1])

    def get_icon_file(self):
        """
        Return the full path to icon for this build action
        """
        filename = self.config.get('icon')
        config_file = self.config.get('configFile')
        if config_file:
            action_dir = os.path.dirname(config_file)
            if filename:
                return os.path.join(action_dir, filename)

    def is_variant_action(self):
        """
        Returns true of this action proxy has any variant attributes.
        """
        return bool(self._variantAttrs)

    def is_variant_attr(self, attr_name: str):
        """
        Return True if the attribute is variant, meaning it is unique
        per each variant instance, and does not exist in the main
        action data.

        Args:
            attr_name (str): The name of a BuildAction attribute
        """
        return attr_name in self._variantAttrs

    def set_is_variant_attr(self, attr_name: str, is_variant: bool):
        """
        Set whether an attr is variant or not.

        Args:
            attr_name (str): The name of a BuildAction attribute
            is_variant (bool): Whether the attribute should be variant or not
        """
        if is_variant:
            self.add_variant_attr(attr_name)
        else:
            self.remove_variant_attr(attr_name)

    def add_variant_attr(self, attr_name: str):
        """
        Add an attribute to the list of variant attributes, removing
        any invariant values for the attribute, and creating
        variant values instead if applicable.

        Args:
            attr_name (str): The name of an action attribute
        """
        if attr_name in self._variantAttrs:
            return

        # add attr to variant attrs list
        self._variantAttrs.append(attr_name)
        for variant in self._variants:
            variant.add_variant_attr(attr_name)

        # if no variants exist, add one
        if self.num_variants() == 0:
            self.add_variant()

        # set the attribute value on all variants using
        # current invariant value if one exists
        if self.has_attr_value(attr_name):
            value = self.get_attr_value(attr_name)
            self.del_attr_value(attr_name)

            for variant in self._variants:
                if not variant.has_attr_value(attr_name):
                    variant.set_attr_value(attr_name, value)

    def remove_variant_attr(self, attr_name: str):
        """
        Remove an attribute from the list of variant attributes,
        copying the value from the first variant into the default set
        of attr values if applicable.

        Args:
            attr_name (str): The name of an action attribute
        """
        if attr_name not in self._variantAttrs:
            return

        # remove from attributes list
        self._variantAttrs.remove(attr_name)

        # transfer first variant value to the invariant values
        if len(self._variants):
            first_variant = self._variants[0]
            if first_variant.has_attr_value(attr_name):
                value = first_variant.get_attr_value(attr_name)
                self.set_attr_value(attr_name, value)

        # remove attr from variant instances
        for variant in self._variants:
            variant.remove_variant_attr(attr_name)

    def get_variant_attrs(self):
        """
        Return the list of all variant attribute names
        """
        return self._variantAttrs

    def clear_variant_attrs(self):
        """
        Remove all variant attributes, copying the values
        from the first variant into the default set of attr values
        if applicable.
        """
        attr_names = self._variantAttrs[:]
        for attrName in attr_names:
            self.remove_variant_attr(attrName)

    def _create_variant(self):
        """
        Return a new BuildActionDataVariant instance
        for use with this action proxy.
        """
        variant = BuildActionDataVariant(action_id=self._action_id)
        for attrName in self._variantAttrs:
            variant.add_variant_attr(attrName)
        return variant

    def get_variant(self, index: int) -> BuildActionDataVariant:
        """
        Return the BuildActionDataVariant instance at an index
        """
        return self._variants[index]

    def get_or_create_variant(self, index) -> BuildActionDataVariant:
        if index >= 0:
            while self.num_variants() <= index:
                self.add_variant()
        return self.get_variant(index)

    def num_variants(self):
        """
        Return how many variants exist on this action proxy
        """
        return len(self._variants)

    def add_variant(self):
        """
        Add a variant of attribute values. Does nothing if there
        are no variant attributes.
        """
        self._variants.append(self._create_variant())

    def insert_variant(self, index):
        """
        Insert a variant of attribute values. Does nothing if there
        are no variant attributes.

        Args:
            index (int): The index at which to insert the new variant
        """
        self._variants.insert(index, self._create_variant())

    def remove_variant_at(self, index):
        """
        Remove a variant of attribute values.

        Args:
            index (int): The index at which to remove the variant
        """
        count = len(self._variants)
        if -count <= index < count:
            del self._variants[index]

    def clear_variants(self):
        """
        Remove all variant instances.
        Does not clear the list of variant attributes.
        """
        self._variants = []

    def serialize(self):
        data = super(BuildActionProxy, self).serialize()
        if self._variantAttrs:
            data['variantAttrs'] = self._variantAttrs
        if self._variants:
            data['variants'] = [
                self.serialize_variant(v) for v in self._variants]
        return data

    def deserialize(self, data):
        super(BuildActionProxy, self).deserialize(data)
        self._variantAttrs = data.get('variantAttrs', [])
        self._variants = [
            self.deserialize_variant(v) for v in data.get('variants', [])]

    def serialize_variant(self, variant):
        data = variant.serialize()
        # prune unnecessary data from the variant for optimization
        del data['id']
        del data['variantAttrs']
        return data

    def deserialize_variant(self, data):
        variant = BuildActionDataVariant()
        # add necessary additional data for deserializing the variant
        data['id'] = self._action_id
        data['variantAttrs'] = self._variantAttrs
        variant.deserialize(data)
        return variant

    def action_iterator(self) -> Iterable['BuildAction']:
        """
        Generator that yields all the BuildActions represented
        by this proxy. If variants are in use, constructs a BuildAction
        for each set of variant attribute values.
        """
        if not self.is_action_id_valid():
            raise Exception("BuildActionProxy has no valid action id: %s" % self)
        if self.is_missing_config():
            raise Exception("Failed to find BuildAction config: %s" %
                            self.get_action_id())

        if self.is_variant_action():
            # ensure there are no invariant values for variant attrs
            for attrName in self._variantAttrs:
                if self.has_attr_value(attrName):
                    LOG.warning("Found invariant value for a variant attr: %s.%s", self.get_action_id(), attrName)

            # create and yield new build actions for each variant
            main_data = self.serialize()
            for variant in self._variants:
                # TODO: update serialization to ensure variants only return
                #       data for the attributes they're supposed to modify
                data = variant.serialize()
                data.update(_copy_data(main_data))
                new_action = BuildAction.from_data(data)
                yield new_action
        else:
            # no variants, just create one action
            yield BuildAction.from_data(_copy_data(self.serialize()))


class BuildAction(BuildActionData):
    """
    The base class for any rigging action that can run during a build.

    Override `run` to perform the rigging operations for the action

    Optionally override `validate` to perform operations that can check
    the validity of the actions properties.
    """

    @staticmethod
    def from_action_id(action_id):
        """
        Create and return a BuildAction by class action_id.

        Args:
            action_id (str): A BuildAction id.
        """
        action_cl = get_build_action_class(action_id)
        if not action_cl:
            raise ValueError(f"Failed to find BuildAction class: {action_id}")

        item = action_cl()
        return item

    @staticmethod
    def from_data(data):
        """
        Create and return a BuildAction based on the given serialized data.

        This is a factory method that automatically determines
        the class to instance using the action id in the data.

        Args:
            data: A dict object containing serialized BuildAction data
        """
        action_cls = get_build_action_class(data['id'])
        if not action_cls:
            raise ValueError(f"Failed to find BuildAction class: {data['id']}")

        item = action_cls()
        item.deserialize(data)
        return item

    def __init__(self):
        super(BuildAction, self).__init__()

        # logger is initialized the first time its accessed
        self._log = None
        # builder is only available during build
        from pulse.blueprints import BlueprintBuilder
        self.builder: Optional[BlueprintBuilder] = None
        # rig is only available during build
        self.rig = None

        # pull action name from the class name
        self._config = _get_build_action_config_for_class(self.__class__)
        if self._config:
            self._actionId = self.config['id']
        else:
            LOG.warning("Constructed an unregistered BuildAction: %s, cannot retrieve config", self.__class__.__name__)
            return

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __getattr__(self, name):
        attr_config = self.get_attr_config(name)
        if attr_config:
            if name in self._attr_values:
                return self._attr_values[name]
            else:
                return self.get_attr_default_value(attr_config)
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def find_action_config(self):
        # do nothing. BuildAction classes automatically retrieve
        # their config on init using the class itself to look up
        # a registered config.
        pass

    def get_logger_name(self):
        """
        Return the name of the logger for this BuildAction
        """
        return 'pulse.action.' + self.get_action_id()

    @property
    def log(self):
        if not self._log:
            self._log = logging.getLogger(self.get_logger_name())
        return self._log

    def get_min_api_version(self):
        """
        Override to return the minimum Maya api version required for this BuildAction.
        This compares against `cmds.about(api=True)`.
        """
        return 0

    def get_rig_metadata(self):
        """
        Return all metadata on the rig being built
        """
        if not self.rig:
            self.log.error('Cannot get rig meta data, no rig is set')
            return {}
        return meta.getMetaData(self.rig, RIG_METACLASS)

    def update_rig_metadata(self, data):
        """
        Add some metadata to the rig being built

        Args:
            data: A dict containing metadata to update on the rig
        """
        if not self.rig:
            self.log.error('Cannot update rig meta data, no rig is set')
            return
        meta.updateMetaData(self.rig, RIG_METACLASS, data)

    def extend_rig_metadata_list(self, key, data):
        """
        Extend a list value in the metadata of the rig being built.

        Args:
            key (str): The metadata key for the list
            data (list): A list of any basic python object to add to the metadata list value
        """
        # get current value for the meta data key
        rig_data = self.get_rig_metadata()
        current_value = rig_data.get(key, [])
        # append or extend the new data
        new_value = list(set(current_value + data))
        # update meta data
        self.update_rig_metadata({key: new_value})

    def update_rig_metadata_dict(self, key, data):
        """
        Update a dict value in the metadata of the rig being built.

        Args:
            key (str): The metadata key for the list
            data (dict): A dict of any basic python objects to update the metadata value with
        """
        # get current value for the meta data key
        rig_data = self.get_rig_metadata()
        value = rig_data.get(key, {})
        # update dict value with the new data
        value.update(data)
        # update meta data
        self.update_rig_metadata({key: value})

    def validate_api_version(self):
        """
        Validate that the current Maya version meets the requirements for this build action
        """
        min_api_version = self.get_min_api_version()
        if min_api_version > 0 and cmds.about(api=True) < min_api_version:
            raise BuildActionError(
                "Maya api version %s is required to use %s" % (min_api_version, self._actionId))

    def run_validate(self):
        """
        Run the validate function and perform some other basic
        checks to make sure the build action is valid for use.
        """
        self.validate_api_version()
        self.validate_attr_values()
        self.validate()

    def validate_attr_values(self):
        """
        Check each action attribute to ensure it has a
        valid value for its attribute type. Checks for things
        like missing nodes or invalid options.
        """
        for attr in self.get_attrs():
            attr_name = attr['name']
            attr_type = attr['type']
            if self.has_attr_value(attr_name):
                attr_value = self.get_attr_value(attr_name)
                if attr_type == 'nodelist':
                    if None in attr_value:
                        raise BuildActionError(
                            '%s contains a missing object' % attr_name)

    def validate(self):
        """
        Validate this build action. Can be implemented
        in subclasses to check the action's config data
        and raise BuildActionErrors if anything is invalid.
        """
        pass

    def run(self):
        """
        Run this build action. Should be implemented
        in subclasses to perform the rigging operation
        that is desired.
        """
        raise NotImplementedError


class BuildStep(object):
    """
    Represents a step to perform when building a Blueprint.
    Steps are hierarchical, but a BuildStep that performs a BuildAction
    cannot have children.
    """

    default_name = 'New Step'

    # TODO (bsayre): consider adding method to change the action type of the current proxy,
    #       whilst preserving or transferring as much attr data as possible

    @staticmethod
    def from_data(data):
        """
        Return a new BuildStep instance created
        from serialized data.

        Args:
            data (dict): Serialized BuildStep data
        """
        new_step = BuildStep()
        new_step.deserialize(data)
        return new_step

    def __init__(self, name=None, action_proxy: BuildActionProxy = None, action_id: str = None):
        # the name of this step (unique among siblings)
        self._name: Optional[str] = None
        # the parent BuildStep
        self._parent: Optional[BuildStep] = None
        # list of child BuildSteps
        self._children: List[BuildStep] = []
        # the BuildActionProxy for this step
        self._action_proxy = action_proxy

        # is this build step currently disabled?
        self.isDisabled = False

        # auto-create a basic BuildActionProxy if an action_id was given
        if action_id:
            self._action_proxy = BuildActionProxy(action_id)

        # set the name, potentially defaulting to the action's name
        self.set_name(name)

    @property
    def name(self):
        return self._name

    def set_name(self, new_name):
        """
        Set the name of the BuildStep, modifying it if necessary
        to ensure that it is unique among siblings.

        Args:
            new_name (str): The new name of the step
        """
        new_name_clean = self.get_clean_name(new_name)
        if self._name != new_name_clean:
            self._name = new_name_clean
            self.ensure_unique_name()

    def get_clean_name(self, name) -> str:
        """
        Return a name for the build step, ensuring one is set if it hasn't
        already been, and cleaning trailing spaces, etc.
        """
        # ensure a name is set
        if not name:
            if self._action_proxy:
                name = self._action_proxy.get_display_name()
            else:
                name = self.default_name
        return name.strip()

    def set_name_from_action(self):
        """
        Set the name of the BuildStep to match the action it contains.
        """
        if self._action_proxy:
            self.set_name(self._action_proxy.get_display_name())

    def is_disabled_in_hierarchy(self):
        """
        Return true if this step or any of its parents are disabled.
        """
        if self.isDisabled:
            return True
        if self._parent:
            return self._parent.is_disabled_in_hierarchy()
        return False

    def is_action(self):
        return self._action_proxy is not None

    @property
    def action_proxy(self) -> BuildActionProxy:
        return self._action_proxy

    def set_action_proxy(self, action_proxy: BuildActionProxy):
        """
        Set a BuildActionProxy for this step. Will fail if the step has any children.

        Args:
            action_proxy: BuildActionProxy
                The new action proxy.
        """
        if self._children:
            LOG.warning("Cannot set a BuildActionProxy on a step with children. Clear all children first")
            return

        self._action_proxy = action_proxy

    def can_have_children(self) -> bool:
        return not self.is_action()

    @property
    def parent(self):
        return self._parent

    def set_parent_internal(self, new_parent: Optional['BuildStep']):
        self._parent = new_parent
        self._on_parent_changed()

    def set_parent(self, new_parent: Optional['BuildStep']):
        """
        Set the parent of this BuildStep, removing it from its old parent if necessary.
        """
        if new_parent and not new_parent.can_have_children():
            raise ValueError(f"Cannot set parent to step that cannot have children: {new_parent}")

        if self._parent is not new_parent:
            if self._parent:
                self._parent.remove_child_internal(self)
                self._parent = None
            if new_parent:
                new_parent.add_child(self)
            else:
                self.set_parent_internal(None)

    def _on_parent_changed(self):
        self.ensure_unique_name()

    @property
    def children(self):
        return self._children

    def __repr__(self):
        return f"<BuildStep '{self.get_display_name()}'>"

    def ensure_unique_name(self):
        """
        Change this step's name to ensure that it is unique among siblings.
        """
        if self._parent:
            siblings = [c for c in self._parent.children if not (c is self)]
            sibling_names = [s.name for s in siblings]
            while self._name in sibling_names:
                self._name = _increment_name(self._name)

    def get_display_name(self) -> str:
        """
        Return the display name for this step.
        """
        if self._action_proxy:
            if self._action_proxy.is_variant_action():
                return f'{self._name} (x{self._action_proxy.num_variants()})'
            else:
                return f'{self._name}'
        else:
            return f'{self._name} ({self.num_children()})'

    def get_color(self):
        """
        Return the color of this BuildStep when represented in the UI
        """
        if self._action_proxy:
            return self._action_proxy.get_color()
        return [1, 1, 1]

    def get_icon_file(self):
        """
        Return the full path to this build step's icon
        """
        if self._action_proxy:
            return self._action_proxy.get_icon_file()
        else:
            pass

    def get_full_path(self):
        """
        Return the full path to this BuildStep.

        Returns:
            A string path to the step
            e.g. 'MyGroupA/MyGroupB/MyBuildStep'
        """
        if self._parent:
            parent_path = self._parent.get_full_path()
            if parent_path:
                return f'{parent_path}/{self._name}'
            else:
                return self._name
        else:
            # a root step, or step without a parent has no path
            return None

    def get_parent_path(self):
        """
        Return the full path to this BuildStep's parent
        """
        if self._parent:
            return self._parent.get_full_path()

    def index_in_parent(self):
        """
        Return the index of this within its parent's list of children.
        """
        if self.parent:
            return self.parent.get_child_index(self)
        else:
            return 0

    def clear_children(self):
        if not self.can_have_children():
            return

        for step in self._children:
            step.set_parent_internal(None)

        self._children = []

    def add_child(self, step: 'BuildStep'):
        if not self.can_have_children():
            return

        if step is self:
            raise ValueError('Cannot add step as child of itself')

        if not isinstance(step, BuildStep):
            raise TypeError(f'Expected BuildStep, got {type(step).__name__}')

        if step not in self._children:
            self._children.append(step)
            step.set_parent_internal(self)

    def add_children(self, steps: List['BuildStep']):
        for step in steps:
            self.add_child(step)

    def remove_child(self, step: 'BuildStep'):
        if not self.can_have_children():
            return

        if step in self._children:
            self._children.remove(step)
            step.set_parent_internal(None)

    def remove_child_internal(self, step):
        if step in self._children:
            self._children.remove(step)

    def remove_children(self, index, count):
        for _ in range(count):
            self.remove_child_at(index)

    def remove_child_at(self, index):
        if not self.can_have_children():
            return

        if index < 0 or index >= len(self._children):
            return

        step = self._children[index]
        step.set_parent_internal(None)

        del self._children[index]

    def remove_from_parent(self):
        """
        Remove this item from its parent, if any.
        """
        if self.parent:
            self.parent.remove_child(self)

    def insert_child(self, index, step: 'BuildStep'):
        if not self.can_have_children():
            return

        if not isinstance(step, BuildStep):
            raise TypeError(f'Expected BuildStep, got {type(step).__name__}')

        if step not in self._children:
            self._children.insert(index, step)
            step.set_parent_internal(self)

    def num_children(self) -> int:
        if not self.can_have_children():
            return 0

        return len(self._children)

    def has_any_children(self):
        return self.num_children() != 0

    def has_parent(self, step: 'BuildStep'):
        """
        Return True if the step is an immediate or distance parent of this step.
        """
        if self.parent:
            if self.parent == step:
                return True
            else:
                return self.parent.has_parent(step)
        return False

    def get_child_at(self, index: int) -> Optional['BuildStep']:
        if not self.can_have_children():
            return

        if index < 0 or index >= len(self._children):
            LOG.error("child index out of range: %d, num children: %d", index, len(self._children))
            return

        return self._children[index]

    def get_child_index(self, step: 'BuildStep'):
        """
        Return the index of a BuildStep within this step's list of children
        """
        if not self.can_have_children():
            return -1

        return self._children.index(step)

    def get_child_by_name(self, name: str) -> Optional['BuildStep']:
        """
        Return a child step by name
        """
        if not self.can_have_children():
            return

        for step in self._children:
            if step.name == name:
                return step

    def get_child_by_path(self, path: str) -> Optional['BuildStep']:
        """
        Return a child step by relative path
        """
        if not self.can_have_children():
            return

        if '/' in path:
            child_name, grand_child_path = path.split('/', 1)
            child = self.get_child_by_name(child_name)
            if child:
                return child.get_child_by_path(grand_child_path)
        else:
            return self.get_child_by_name(path)

    def child_iterator(self) -> Iterable['BuildStep']:
        """
        Generator that yields all children, recursively.
        """
        if not self.can_have_children():
            return
        for child in self._children:
            if child.isDisabled:
                continue
            yield child
            for descendant in child.child_iterator():
                yield descendant

    def action_iterator(self) -> Iterable[BuildAction]:
        """
        Return a generator that yields all actions for this step.
        """
        if self._action_proxy:
            for elem in self._action_proxy.action_iterator():
                yield elem

    def serialize(self):
        """
        Return this BuildStep as a serialized dict object
        """
        data = UnsortableOrderedDict()
        data['name'] = self._name

        if self.isDisabled:
            data['isDisabled'] = True

        if self._action_proxy:
            data['action'] = self._action_proxy.serialize()

        if self.num_children() > 0:
            # TODO: perform a recursion loop check
            data['children'] = [c.serialize() for c in self._children]

        return data

    def deserialize(self, data):
        """
        Load configuration of this BuildStep from data

        Args:
            data: A dict containing serialized data for this step
        """
        self.isDisabled = data.get('isDisabled', False)

        if 'action' in data:
            new_action_proxy = BuildActionProxy()
            new_action_proxy.deserialize(data['action'])
            self.set_action_proxy(new_action_proxy)
        else:
            self._action_proxy = None

        # set name after action, so that if no name has
        # been set yet, it will be initialized with the name
        # of the action
        self.set_name(data.get('name', None))

        # TODO: warn if throwing away children in a rare case that
        #       both a proxy and children existed (maybe data was manually created).
        if self.can_have_children():
            # detach any existing children
            self.clear_children()
            # deserialize all children, and connect them to this parent
            self._children = [BuildStep.from_data(c) for c in data.get('children', [])]
            for child in self._children:
                if child:
                    child.set_parent_internal(self)

    @staticmethod
    def get_topmost_steps(steps: List['BuildStep']) -> List['BuildStep']:
        """
        Return a copy of the list of BuildSteps that doesn't include
        any BuildSteps that have a parent or distant parent in the list.
        """

        def has_any_parent(step: BuildStep, parents: List['BuildStep']):
            for parent in parents:
                if step != parent and step.has_parent(parent):
                    return True
            return False

        top_steps = []

        for step in steps:
            if not has_any_parent(step, steps):
                top_steps.append(step)

        return top_steps
