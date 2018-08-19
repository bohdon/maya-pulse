

from collections import OrderedDict
import pymetanode as meta
import pymel.core as pm

from pulse.vendor import yaml
from pulse.vendor.yaml.composer import Composer
from pulse.vendor.yaml.constructor import Constructor
from pulse.vendor.yaml.emitter import Emitter
from pulse.vendor.yaml.parser import Parser
from pulse.vendor.yaml.reader import Reader
from pulse.vendor.yaml.resolver import Resolver
from pulse.vendor.yaml.scanner import Scanner
from pulse.vendor.yaml.serializer import Serializer

__all__ = [
    'UnsortableList',
    'UnsortableOrderedDict',
    'PulseDumper',
    'PulseLoader',
    'PulseRepresenter',
    'PulseConstructor',
]


class UnsortableList(list):
    def sort(self, *args, **kwargs):
        pass


class UnsortableOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return UnsortableList(OrderedDict.items(self, *args, **kwargs))


class PulseRepresenter(yaml.representer.SafeRepresenter):

    def represent_node(self, data):
        """
        Represent a PyMel node as its UUID str
        """
        uuid = str(meta.getUUID(data))
        return self.represent_str(uuid)


PulseRepresenter.add_representer(
    UnsortableOrderedDict,
    PulseRepresenter.represent_dict)

PulseRepresenter.add_multi_representer(
    pm.nt.DagNode,
    PulseRepresenter.represent_node
)


class PulseConstructor(yaml.loader.SafeConstructor):

    def construct_pulse_str(self, node):
        """
        Construct str data. Handles converting UUIDs
        back into PyNodes.
        """
        value = self.construct_yaml_str(node)
        if meta.isUUID(value):
            return meta.findNodeByUUID(value)
        else:
            return value


PulseConstructor.add_constructor(
    u'tag:yaml.org,2002:str',
    PulseConstructor.construct_pulse_str)


class PulseDumper(Emitter, Serializer, PulseRepresenter, Resolver):

    def __init__(self, stream,
                 default_style=None, default_flow_style=None,
                 canonical=None, indent=None, width=None,
                 allow_unicode=None, line_break=None,
                 encoding=None, explicit_start=None, explicit_end=None,
                 version=None, tags=None):
        Emitter.__init__(self, stream, canonical=canonical,
                         indent=indent, width=width,
                         allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                            explicit_start=explicit_start, explicit_end=explicit_end,
                            version=version, tags=tags)
        PulseRepresenter.__init__(self, default_style=default_style,
                                  default_flow_style=default_flow_style)
        Resolver.__init__(self)


class PulseLoader(Reader, Scanner, Parser, Composer, PulseConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        PulseConstructor.__init__(self)
        Resolver.__init__(self)
