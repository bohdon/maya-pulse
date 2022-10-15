import logging
import os
import re
from typing import List, Iterable, Optional, Any

import maya.cmds as cmds

from .vendor import pymetanode as meta
from .rigs import RIG_METACLASS
from .serializer import UnsortableOrderedDict

LOG = logging.getLogger(__name__)
LOG_LEVEL_KEY = 'PYLOG_%s' % LOG.name.split('.')[0].upper()
LOG.setLevel(os.environ.get(LOG_LEVEL_KEY, 'INFO').upper())

BUILD_ACTION_MAP = {}


class BuildActionSpec(object):
    """
    Contains information about a registered build action class and its config.
    """

    def __init__(self, config: dict, file_path: str, action_cls: type['BuildAction'], module):
        # the action's config info as defined in the yaml file
        self.config = config
        # the full path to the actions config file
        self.file_path = file_path
        # the BuildAction subclass defined in the python file
        self.action_cls = action_cls
        # the python module containing the BuildAction
        self.module = module
        # the optional custom editor form class
        self.editor_form_cls = self._find_editor_form_class()

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.get_action_id()}'>"

    def is_valid(self) -> bool:
        return self.get_action_id() and self.action_cls is not None

    def is_equal(self, other: 'BuildActionSpec') -> bool:
        """
        Return true if this action spec is the same as another.
        """
        return self.action_cls == other.action_cls and self.file_path == other.file_path

    def get_action_id(self):
        return self.config.get('id')

    def _find_editor_form_class(self):
        """
        Find the BuildActionProxyForm class to use for this action, if any.
        """
        from pulse.ui.actioneditor import BuildActionProxyForm

        cls_name = self.config.get('editorFormClass')
        if not cls_name:
            # no custom editor form class was specified
            return

        if self.module and hasattr(self.module, cls_name):
            obj = getattr(self.module, cls_name)
            if isinstance(obj, type) and issubclass(obj, BuildActionProxyForm):
                # store the editor form class object in the config
                return obj
            else:
                LOG.error("%s is not a valid BuildActionProxyForm subclass", cls_name)
        else:
            LOG.error("Failed to find a BuildActionProxyForm named '%s' in module %s", cls_name, self.module)


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


class BuildActionRegistry(object):
    """
    A registry that contains all Build Actions available for use.
    """

    # the shared registry instance, accessible from `BuildActionRegistry.get()`
    _instance = None

    @classmethod
    def get(cls):
        """
        Return the main BuildActionRegistry
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # map of all registered actions by id
        self._registered_actions: dict[str, BuildActionSpec] = {}

    def add_action(self, action_spec: BuildActionSpec):
        """
        Add a BuildActionSpec to the registry.
        """
        if not action_spec.is_valid():
            LOG.error("BuildActionSpec is not valid: %s", action_spec)
            return

        # store in action map by id
        action_id = action_spec.get_action_id()
        if action_id in self._registered_actions:
            if self._registered_actions[action_id].is_equal(action_spec):
                # this action spec is already registered
                return
            else:
                # attempting to register a new action spec with the same id
                LOG.error("A BuildAction already exists with id: %s", action_id)
                return

        self._registered_actions[action_id] = action_spec

    def remove_action(self, action_id):
        """
        Remove a BuildActionSpec from the registry by id.
        """
        if action_id in self._registered_actions:
            del self._registered_actions[action_id]

    def remove_all(self):
        """
        Remove all actions from this registry.
        """
        self._registered_actions = {}

    def get_action_map(self) -> dict[str, BuildActionSpec]:
        """
        Return the registered BuildActionSpecs map, indexed by action ids.
        """
        return self._registered_actions

    def get_all_actions(self) -> Iterable[BuildActionSpec]:
        """
        Return all registered BuildActionSpecs.
        """
        return self._registered_actions.values()

    def get_action_ids(self) -> Iterable[str]:
        """
        Return all registered action ids.
        """
        return self._registered_actions.keys()

    def find_action(self, action_id: str) -> Optional[BuildActionSpec]:
        """
        Find a BuildActionSpec by action id
        """
        if action_id in self._registered_actions:
            return self._registered_actions[action_id]

    def find_action_by_class(self, action_cls: type['BuildAction']) -> Optional[BuildActionSpec]:
        """
        Find a BuildActionSpec by action class.
        """
        for config in self._registered_actions.values():
            if config.action_cls == action_cls:
                return config


class BuildActionError(Exception):
    """
    A BuildAction was misconfigured or failed during build
    """
    pass


class BuildActionAttributeType(object):
    """
    Constants defining the build action attribute types.
    """
    UNKNOWN = None
    BOOL = 'bool'
    INT = 'int'
    FLOAT = 'float'
    VECTOR3 = 'vector3'
    STRING = 'string'
    STRING_LIST = 'stringlist'
    OPTION = 'option'
    NODE = 'node'
    NODE_LIST = 'nodelist'


class BuildActionAttribute(object):
    """
    A single attribute of a build action.
    Contains the attributes config as well as current value and validation logic.

    When creating instances you should use `BuildActionAttribute.from_spec()` to ensure
    the appropriate subclass will be instanced based on the attributes type, since
    each subclass has its own validation logic, etc.
    """

    # the attribute type that this class is designed to handle
    class_attr_type: Optional[str] = BuildActionAttributeType.UNKNOWN

    # cached map of attribute types to BuildActionAttribute classes for faster lookup
    _attr_class_map: dict[Optional[str]: type['BuildActionAttribute']] = {}

    @classmethod
    def from_spec(cls, name: str, action_spec: BuildActionSpec = None):
        """
        Create a BuildActionAttribute object from a name and spec, using the
        appropriate class based on the attribute type.
        """
        # Note: for some reason, logging a warning or printing anything during the construction
        #       of a BuildActionAttribute causes Maya to crash during blueprint reload.
        attr_type: str = cls._find_attr_config(name, action_spec).get('type')
        subclass: Optional[type[BuildActionAttribute]] = cls._find_attr_class(attr_type)
        if subclass:
            return subclass(name, action_spec)
        else:
            return BuildActionAttribute(name, action_spec)

    @classmethod
    def _find_attr_class(cls, attr_type):
        # check in cache first
        if attr_type in cls._attr_class_map:
            return cls._attr_class_map[attr_type]
        # iterate subclasses, and cache if found
        for subclass in cls.__subclasses__():
            if subclass.class_attr_type == attr_type:
                cls._attr_class_map[attr_type] = subclass
                return subclass

    def __init__(self, name: str, action_spec: BuildActionSpec = None):
        # the name of the attribute
        self._name = name
        # the action spec with config containing information about the attribute
        self.action_spec = action_spec
        # the cached config for this attribute
        self._attr_config: Optional[dict] = None
        # the current value of the attribute
        self._value = None
        # whether the attributes value is currently valid
        self._is_valid = True
        # the current reason the value is not valid, if any
        self._invalid_reason: Optional[str] = None

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.get_action_id()}.{self.name}'>"

    def is_valid_attribute(self) -> bool:
        """
        Return true if this attribute is a known and valid attribute for a build action.
        Will be false if the attribute is a placeholder left behind for a missing attribute.
        """
        return self.action_spec is not None and self.name is not None

    @classmethod
    def _find_attr_config(cls, attr_name: str, action_spec: BuildActionSpec) -> dict:
        """
        Find and return the config for an attribute from an action spec.
        """
        if action_spec:
            attrs_config = action_spec.config.get('attrs', [])
            for attr_config in attrs_config:
                if attr_config.get('name') == attr_name:
                    return attr_config
        return {}

    def get_action_id(self) -> Optional[str]:
        if self.action_spec:
            return self.action_spec.get_action_id()

    @property
    def config(self) -> dict:
        """
        Return the config for this attribute.
        """
        if self._attr_config is None:
            self._attr_config = self._find_attr_config(self.name, self.action_spec)
        return self._attr_config

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self.config.get('type')

    @property
    def description(self):
        return self.config.get('description')

    @property
    def is_optional(self):
        return self.config.get('optional', False)

    @property
    def default_value(self) -> Any:
        """
        Return the default value of the attribute.
        """
        # 'value' key represents the default value of the attribute in the config
        if 'value' in self.config:
            return self.config['value']
        return self.get_type_default_value()

    def get_type_default_value(self):
        """
        Return the default value for any attribute of this type.
        Does not use the config defined default.
        """
        return None

    def get_value(self):
        """
        The current value of the attribute.
        Returns the default value if a different value has not been set.
        """
        if self._value is not None:
            return self._value
        return self.default_value

    def set_value(self, new_value):
        if self.is_acceptable_value(new_value):
            if new_value == self.default_value:
                # clear the value when default, so it doesn't serialize
                self.clear_value()
            else:
                self._value = new_value
        else:
            LOG.error(f"'{new_value}' is not an acceptable value for attribute'{self.name}' ({self.type})")

    def is_acceptable_value(self, new_value):
        """
        Return true if a value is acceptable. This doesn't mean the value won't
        be invalid for some other reason, just that it's the correct type and
        the attribute can be set to it.
        """
        return True

    def is_value_set(self):
        """
        Return true if the value of this attribute has been explicitly set,
        false if it is the default value.
        """
        return self._value is not None

    def validate(self):
        """
        Validate the attribute, checking its current value and other requirements
        and storing the reason it is invalid if applicable.
        """
        if self.class_attr_type == BuildActionAttributeType.UNKNOWN:
            self._invalid_reason = 'unknown_type'
            self._is_valid = False
        else:
            self._invalid_reason = None
            self._is_valid = True

    def is_value_valid(self) -> bool:
        """
        Return true if the current value of this attribute is valid.
        Must call `validate` first to check the value, call `get_invalid_reason`
        to determine why the attribute is invalid if applicable.
        """
        return self._is_valid

    def get_invalid_reason(self) -> str:
        return self._invalid_reason

    def clear_value(self):
        """
        Clear the assigned value of this attribute, resetting it to the default value.
        """
        self._value = None


class BuildActionBoolAttribute(BuildActionAttribute):
    """
    A bool attribute.
    """

    class_attr_type = BuildActionAttributeType.BOOL

    def get_type_default_value(self):
        return False

    def is_acceptable_value(self, new_value):
        return new_value in (False, True)


class BuildActionIntAttribute(BuildActionAttribute):
    """
    An int attribute.
    """

    class_attr_type = BuildActionAttributeType.INT

    def get_type_default_value(self):
        return 0

    def is_acceptable_value(self, new_value):
        return isinstance(new_value, int)


class BuildActionFloatAttribute(BuildActionAttribute):
    """
    A float attribute.
    """

    class_attr_type = BuildActionAttributeType.FLOAT

    def get_type_default_value(self):
        return 0.0

    def is_acceptable_value(self, new_value):
        return isinstance(new_value, (int, float))


class BuildActionVector3Attribute(BuildActionAttribute):
    """
    A vector attribute with 3 components.
    """

    class_attr_type = BuildActionAttributeType.VECTOR3

    def get_type_default_value(self):
        return [0.0, 0.0, 0.0]

    def is_acceptable_value(self, new_value):
        return (isinstance(new_value, list) and
                len(new_value) == 3 and
                all([isinstance(v, (int, float)) for v in new_value]))


class BuildActionStringAttribute(BuildActionAttribute):
    """
    A string attribute.
    """

    class_attr_type = BuildActionAttributeType.STRING

    def get_type_default_value(self):
        return ''

    def is_acceptable_value(self, new_value):
        return isinstance(new_value, str)

    def validate(self):
        # unless explicitly optional, there must be a value (default is accepted)
        if not self.is_optional and not self.get_value():
            self._invalid_reason = 'required'
            self._is_valid = False
        else:
            self._invalid_reason = None
            self._is_valid = True


class BuildActionStringListAttribute(BuildActionAttribute):
    """
    An attribute that stores a list of strings.
    """

    class_attr_type = BuildActionAttributeType.STRING_LIST

    def get_type_default_value(self):
        return []

    def is_acceptable_value(self, new_value):
        return isinstance(new_value, list) and all([isinstance(v, str) for v in new_value])


class BuildActionOptionAttribute(BuildActionAttribute):
    """
    An attribute that allows selecting from a list of options. Value is an int.
    """

    class_attr_type = BuildActionAttributeType.OPTION

    def get_type_default_value(self):
        return 0

    def is_acceptable_value(self, new_value):
        return isinstance(new_value, int)

    def validate(self):
        value = self.get_value()
        num_options = len(self.config.get('options', []))
        if value < 0 or value >= num_options:
            self._invalid_reason = 'out_of_range'
            self._is_valid = False
            print(f'0 <= {self.get_value()} < {num_options}, {self}')
        else:
            self._invalid_reason = None
            self._is_valid = True


class BuildActionNodeAttribute(BuildActionAttribute):
    """
    An attribute that references a single node.
    """

    class_attr_type = BuildActionAttributeType.NODE

    def get_type_default_value(self):
        return None

    def is_acceptable_value(self, new_value):
        import pymel.core as pm
        return new_value is None or isinstance(new_value, pm.nt.DependNode)

    def validate(self):
        # unless explicitly optional, a value must be set
        if not self.is_optional and not self.is_value_set():
            self._invalid_reason = 'required'
            self._is_valid = False
        else:
            self._invalid_reason = None
            self._is_valid = True


class BuildActionNodeListAttribute(BuildActionAttribute):
    """
    An attribute that references a list of nodes.
    """

    class_attr_type = BuildActionAttributeType.NODE_LIST

    def get_type_default_value(self):
        return []

    def is_acceptable_value(self, new_value):
        import pymel.core as pm
        return isinstance(new_value, list) and all([isinstance(v, pm.nt.DependNode) for v in new_value])

    def validate(self):
        # unless explicitly optional, a value must be set
        if not self.is_optional and not self.is_value_set():
            self._invalid_reason = 'required'
            self._is_valid = False
            return

        self._invalid_reason = None
        self._is_valid = True


class BuildActionData(object):
    """
    Contains attribute values for an action to be executed during a build step.
    """

    def __init__(self, action_id: str = None):
        # the unique id of this action, used to identify the action when serialized
        self._action_id: str = action_id
        # the BuildActionSpec containing config and other info
        self._action_spec: Optional[BuildActionSpec] = None
        # true if the action_id is set, but spec was not found, indicating an error
        self._is_missing_spec = False
        # the list of attributes and their values for this action
        self._attrs: dict[str, BuildActionAttribute] = {}

        if self._action_id:
            self.find_action_spec()

        self._init_attrs()

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.action_id}'>"

    def _init_attrs(self):
        """
        Initialize the set of attributes for this action data.
        """
        # clear existing attributes
        self._attrs = {}
        # add all attributes in the config
        attr_names = [a.get('name') for a in self.config.get('attrs', [])]
        self.add_attrs(attr_names)

    @property
    def action_id(self) -> str:
        """
        Return unique the id of the action.
        """
        return self._action_id

    @property
    def action_spec(self) -> BuildActionSpec:
        """
        Return the BuildActionSpec for this action.
        """
        return self._action_spec

    @property
    def config(self) -> dict:
        if self._action_spec:
            return self._action_spec.config
        return {}

    def is_valid(self) -> bool:
        """
        Return True if there is a valid spec for this action
        """
        return self._action_spec is not None

    def is_action_id_valid(self) -> bool:
        return self._action_id is not None

    def is_missing_spec(self) -> bool:
        """
        Is there no action spec config for the current action_id?
        This may be true if an action was renamed or not registered.
        """
        return self._is_missing_spec

    def get_short_action_id(self) -> str:
        """
        Return the last part of the action's id, after any '.'
        """
        if self._action_id:
            return self._action_id.split('.')[-1]

    def find_action_spec(self):
        """
        Find the action spec for this data using the current action_id.
        """
        self._action_spec = BuildActionRegistry.get().find_action(self._action_id)
        if self._action_spec:
            self._is_missing_spec = False
        else:
            self._is_missing_spec = True
            LOG.warning(f"Failed to find action spec for '%s'", self._action_id)

    def num_attrs(self) -> int:
        """
        Return the number of attributes that this BuildAction has
        """
        return len(self._attrs)

    def get_attrs(self) -> dict[str, BuildActionAttribute]:
        """
        Return all attributes for this BuildAction class.
        """
        return self._attrs

    def get_attr_names(self) -> Iterable[str]:
        """
        Return a list of attribute names for this BuildAction class
        """
        for attr in self._attrs.values():
            yield attr.name

    def add_attr(self, name: str) -> BuildActionAttribute:
        """
        Add an action attribute. Does nothing if the attribute already exists.
        """
        if name not in self._attrs:
            attr = BuildActionAttribute.from_spec(name, self._action_spec)
            self._attrs[name] = attr
            return attr
        else:
            return self._attrs[name]

    def add_attrs(self, attr_names=None):
        """
        Add multiple attributes.
        """
        if attr_names is None:
            attr_names = []

        for attr_name in attr_names:
            self.add_attr(attr_name)

    def remove_attr(self, name: str):
        """
        Remove an action attribute. Does nothing if the attribute does not exist.
        """
        if name in self._attrs:
            del self._attrs[name]

    def get_attr(self, name: str):
        """
        Return an attribute by name.
        """
        return self._attrs.get(name)

    def has_attr(self, name: str) -> bool:
        """
        Return True if this action data has an attribute.
        """
        return name in self._attrs

    def serialize(self):
        """
        Return this BuildActionData as a serialized dict object
        """
        data = UnsortableOrderedDict()
        data['id'] = self._action_id
        # serialize all attributes
        if self.is_valid():
            for attr_name, attr in self._attrs.items():
                # don't serialize default attribute values
                if attr.is_value_set():
                    data[attr_name] = attr.get_value()
        return data

    def deserialize(self, data):
        """
        Set all values on this BuildActionData from data

        Args:
            data: A dict containing serialized data for this action
        """
        self._action_id = data['id']

        # update spec
        if self._action_id:
            self.find_action_spec()

        # reset attributes
        self._init_attrs()

        # load all attribute values
        if self.is_valid():
            for attr_name, attr in self._attrs.items():
                if attr_name in data:
                    attr.set_value(data[attr_name])

        elif len(data) > 1:
            # if spec wasn't found didn't load, don't throw away the attribute values
            LOG.warning("Failed to find BuildActionSpec '%s', action values will be preserved.", self._action_id)
            for attr_name, value in data.items():
                if attr_name not in self._attrs:
                    attr = BuildActionAttribute.from_spec(attr_name)
                    attr.set_value(value)
                    self._attrs[attr_name] = value


class BuildActionDataVariant(BuildActionData):
    """
    Contains a partial set of attribute values.
    """

    def __init__(self, action_id: str = None, attr_names: List[str] = None):
        if attr_names is None:
            attr_names = []

        # names of all attributes that are in this variant, only used during init
        self._initial_attr_names = attr_names

        super(BuildActionDataVariant, self).__init__(action_id=action_id)

    def _init_attrs(self):
        """
        Don't automatically initialize all attributes in a variant,
        only those that are marked as variant.
        """
        # clear existing attributes
        self._attrs = {}
        # add the specified initial attribute names available to this variant
        self.add_attrs(self._initial_attr_names)
        # clear temporary property, so it isn't used or confused for anything
        self._initial_attr_names = []

    def serialize(self):
        data = super(BuildActionDataVariant, self).serialize()
        # store the subset of attribute names available to this variant.
        data['variantAttrs'] = self.get_attr_names()
        return data

    def deserialize(self, data):
        # restore the set of attributes available to the variant,
        # they will be initted during the super deserialize
        self._initial_attr_names = data.get('variantAttrs', [])

        super(BuildActionDataVariant, self).deserialize(data)


class BuildActionProxy(BuildActionData):
    """
    Acts as a stand-in for a BuildAction during Blueprint editing.
    Contains all attribute values for the configured action, which are used
    to create real BuildActions at build time.

    The proxy can represent multiple BuildActions by adding 'variants'.
    This allows the user to create multiple actions where only the values that are
    unique per variant are set, and the remaining attributes will be the same on all actions.

    The proxy provides a method `action_iterator` which performs the
    actual construction of BuildActions for use at build time.
    """

    def __init__(self, action_id=None):
        super(BuildActionProxy, self).__init__(action_id=action_id)
        # names of all attribute names that are available to set on a variant
        self._variant_attr_names: List[str] = []
        # list of all variants containing their own subset of attributes
        self._variants: List[BuildActionDataVariant] = []

    def get_display_name(self):
        """
        Return the display name of the BuildAction.
        """
        return self.config.get('displayName', self.get_short_action_id())

    def get_color(self):
        """
        Return the color of this action when represented in the UI
        """
        if self.is_missing_spec():
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
        return bool(self._variant_attr_names)

    def is_variant_attr(self, attr_name: str):
        """
        Return True if the attribute is variant, meaning it can have a different value in each variant.
        """
        return attr_name in self._variant_attr_names

    def add_variant_attr(self, attr_name: str):
        """
        Add an attribute to the list of variant attributes, removing any invariant values
        for the attribute, and creating variant values instead.
        """
        if attr_name in self._variant_attr_names:
            # already variant
            return

        self._variant_attr_names.append(attr_name)

        # add attr for all variants
        for variant in self._variants:
            variant.add_attr(attr_name)

        # if no variants exist, add at least one
        if self.num_variants() == 0:
            self.add_variant()

        # set all variants to the current base value
        # TODO: allow attribute types to define whether this logic applies
        base_attr = self.get_attr(attr_name)
        if base_attr and base_attr.is_value_set():
            base_value = base_attr.get_value()

            # set the same value on all variants
            for variant in self._variants:
                variant_attr = variant.get_attr(attr_name)
                if variant_attr:
                    variant_attr.set_value(base_value)

            # clear the invariant value
            base_attr.clear_value()

    def remove_variant_attr(self, attr_name: str):
        """
        Remove an attribute from the list of variant attributes, copying the value from the
        first variant into the default set of attr values if applicable.
        """
        if attr_name not in self._variant_attr_names:
            # already invariant
            return

        self._variant_attr_names.remove(attr_name)

        # transfer first variant value to the invariant values
        if self._variants:
            first_variant = self._variants[0]
            variant_attr = first_variant.get_attr(attr_name)
            base_attr = self.get_attr(attr_name)
            if variant_attr and base_attr:
                base_attr.set_value(variant_attr.get_value())

        if not self.is_variant_action():
            # no longer a variant action, remove all variants
            self.clear_variants()
        else:
            # remove attr from all variants
            for variant in self._variants:
                variant.remove_attr(attr_name)

    def get_variant_attr_names(self):
        """
        Return the list of all variant attribute names
        """
        return self._variant_attr_names

    def _create_variant(self) -> BuildActionDataVariant:
        """
        Return a new BuildActionDataVariant for use with this action proxy.
        """
        variant = BuildActionDataVariant(action_id=self._action_id, attr_names=self._variant_attr_names)
        return variant

    def get_variant(self, index: int) -> BuildActionDataVariant:
        """
        Return the BuildActionDataVariant at an index.
        """
        return self._variants[index]

    def get_variants(self) -> Iterable[BuildActionDataVariant]:
        """
        Return all BuildActionDataVariants in this proxy.
        """
        for variant in self._variants:
            yield variant

    def get_or_create_variant(self, index: int) -> BuildActionDataVariant:
        if index >= 0:
            while self.num_variants() <= index:
                self.add_variant()
        return self.get_variant(index)

    def num_variants(self) -> int:
        """
        Return how many variants exist on this action proxy
        """
        return len(self._variants)

    def add_variant(self):
        """
        Add a variant of attribute values. Does nothing if there are no variant attributes.
        """
        if self.is_variant_action():
            self._variants.append(self._create_variant())

    def insert_variant(self, index):
        """
        Insert a variant of attribute values. Does nothing if there are no variant attributes.

        Args:
            index (int): The index at which to insert the new variant
        """
        if self.is_variant_action():
            self._variants.insert(index, self._create_variant())

    def remove_variant_at(self, index: int):
        """
        Remove a variant by index.
        """
        count = len(self._variants)
        if -count <= index < count:
            del self._variants[index]

    def clear_variants(self):
        """
        Remove all variants. Does not clear the list of variant attributes.
        """
        self._variants = []

    def serialize(self):
        data = super(BuildActionProxy, self).serialize()
        if self._variant_attr_names:
            data['variantAttrs'] = self._variant_attr_names
        if self._variants:
            data['variants'] = [self.serialize_variant(v) for v in self._variants]
        return data

    def deserialize(self, data):
        super(BuildActionProxy, self).deserialize(data)
        self._variant_attr_names = data.get('variantAttrs', [])
        self._variants = [self.deserialize_variant(v) for v in data.get('variants', [])]

    def serialize_variant(self, variant):
        """
        Serialize a variant for storing in this action's data.
        Removes redundant information that is the same for all variants like id and attribute list.
        """
        data = variant.serialize()
        # prune unnecessary data from the variant for optimization
        del data['id']
        del data['variantAttrs']
        return data

    def deserialize_variant(self, data):
        """
        Deserialize a variant from this action's 'variantAttrs' data.
        Injects missing information that are the same for all variants like id and attribute list.
        """
        variant = BuildActionDataVariant()
        # add necessary additional data for deserializing the variant
        data['id'] = self._action_id
        data['variantAttrs'] = self._variant_attr_names
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
        if self.is_missing_spec():
            raise Exception("Failed to find BuildAction config: %s" % self.action_id)

        if self.is_variant_action():
            # warn if there are invariant base values set on variant attrs
            for attr_name in self._variant_attr_names:
                attr = self.get_attr(attr_name)
                if attr.is_value_set():
                    LOG.warning("Found invariant value for a variant attr: %s.%s", self.action_id, attr_name)

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
    def from_action_id(action_id: str) -> Optional['BuildAction']:
        """
        Create and return a BuildAction by class action_id.
        """
        action_spec = BuildActionRegistry.get().find_action(action_id)
        if not action_spec:
            LOG.error(f"BuildAction.from_action_id: Failed to find BuildAction class for id '{action_id}'")
            return

        action = action_spec.action_cls()
        return action

    @staticmethod
    def from_data(data) -> Optional['BuildAction']:
        """
        Create and return a BuildAction based on the given serialized data.

        This is a factory method that automatically determines
        the class to instance using the action id in the data.

        Args:
            data: A dict object containing serialized BuildAction data
        """
        action_id = data.get('id')
        if not action_id:
            LOG.error(f"BuildAction.from_data: Invalid data, missing 'id' key: %s", data)
            return

        action = BuildAction.from_action_id(action_id)
        if not action:
            return

        action.deserialize(data)
        return action

    def __init__(self):
        super(BuildAction, self).__init__()

        # logger is initialized the first time its accessed
        self._log = None
        # builder is only available during build
        from pulse.blueprints import BlueprintBuilder
        self.builder: Optional[BlueprintBuilder] = None
        # rig is only available during build
        self.rig = None

        # retrieve action spec using this class
        self._action_spec = BuildActionRegistry.get().find_action_by_class(self.__class__)
        if self._action_spec:
            self._action_id = self._action_spec.get_action_id()
        else:
            LOG.warning("Constructed an unregistered BuildAction: %s, cannot retrieve config", self.__class__.__name__)
            return

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __getattr__(self, name: str):
        attr = self.get_attr(name)
        if attr:
            return attr.get_value()
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def find_action_spec(self):
        # do nothing. BuildAction classes automatically retrieve
        # their config on init using the class itself to look up
        # a registered config.
        pass

    def get_logger_name(self):
        """
        Return the name of the logger for this BuildAction
        """
        return f'pulse.action.{self.action_id}'

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
        Check each action attribute to ensure it has a valid value for its attribute type.
        Checks for things like missing nodes or invalid options.
        """
        for attr_name, attr in self._attrs.items():
            # TODO: leave this implementation up to the attribute class type
            if attr.type == 'nodelist':
                if None in attr.get_value():
                    raise BuildActionError('%s contains a missing object' % attr_name)

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
        return f"<{self.__class__.__name__} '{self.get_display_name()}'>"

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
        return [1.0, 1.0, 1.0]

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
