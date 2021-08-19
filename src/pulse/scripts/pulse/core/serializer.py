from collections import OrderedDict

import pymel.core as pm

import pymetanode as meta
from ..vendor import yaml
from ..vendor.yaml.composer import Composer
from ..vendor.yaml.constructor import SafeConstructor
from ..vendor.yaml.emitter import Emitter
from ..vendor.yaml.parser import Parser
from ..vendor.yaml.reader import Reader
from ..vendor.yaml.representer import SafeRepresenter
from ..vendor.yaml.resolver import Resolver
from ..vendor.yaml.scanner import Scanner
from ..vendor.yaml.serializer import Serializer


class PulseDumper(Emitter, Serializer, SafeRepresenter, Resolver):

    def __init__(self, stream,
                 default_style=None, default_flow_style=False,
                 canonical=None, indent=None, width=None,
                 allow_unicode=None, line_break=None,
                 encoding=None, explicit_start=None, explicit_end=None,
                 version=None, tags=None, sort_keys=True):
        Emitter.__init__(self, stream, canonical=canonical,
                         indent=indent, width=width,
                         allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                            explicit_start=explicit_start, explicit_end=explicit_end,
                            version=version, tags=tags)
        SafeRepresenter.__init__(self, default_style=default_style,
                                 default_flow_style=default_flow_style, sort_keys=sort_keys)
        Resolver.__init__(self)


class PulseLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)


class UnsortableList(list):
    def sort(self, *args, **kwargs):
        pass


class UnsortableOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return UnsortableList(OrderedDict.items(self, *args, **kwargs))


PulseDumper.add_representer(
    UnsortableOrderedDict,
    PulseDumper.represent_dict)


class DagNodeTag(yaml.YAMLObject):
    """
    Maya Node reference tag for yaml
    """
    yaml_tag = u'!node'

    @classmethod
    def from_yaml(cls, loader, node):
        if node.value == 'null':
            return None
        else:
            return meta.findNodeByUUID(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        if data:
            uuid = str(meta.getUUID(data))
            return dumper.represent_scalar(cls.yaml_tag, uuid)
        else:
            return dumper.represent_scalar(cls.yaml_tag, 'null')


PulseLoader.add_constructor(
    DagNodeTag.yaml_tag, DagNodeTag.from_yaml)
PulseDumper.add_multi_representer(
    pm.nt.DagNode, DagNodeTag.to_yaml)


def serializeAttrValue(value):
    return meta.encodeMetaData(value)


def deserializeAttrValue(value):
    return meta.decodeMetaData(value)
