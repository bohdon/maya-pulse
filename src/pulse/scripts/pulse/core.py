
import pymel.core as pm

import os
import logging
import time
import yaml

import pymetanode as meta

from . import version


__all__ = [
    'Blueprint',
    'BuildAction',
    'BuildActionError',
    'BuildGroup',
    'BuildItem',
    'getActionClass',
    'getBuildItemClass',
    'getRegisteredActions',
    'isBlueprintNode',
    'loadBlueprintFromNode',
    'registerActions',
]


LOG = logging.getLogger(__name__)


BLUEPRINT_METACLASS = 'pulse_blueprint'
BLUEPRINT_VERSION = version.__version__
BLUEPRINT_NODENAME = 'pulse_blueprint'

BUILDITEM_TYPEMAP = {}



def isBlueprintNode(node):
    """
    Return whether the given node is a Blueprint node
    """
    return meta.hasMetaClass(node, BLUEPRINT_METACLASS)


def loadBlueprintFromNode(node):
    """
    Load a Blueprint from a node

    Args:
        node: A PyNode containing pulse blueprint data
    """
    if isBlueprint(node):
        data = meta.getMetaData(node, BLUEPRINT_METACLASS)
        result = Blueprint.fromData(data)
        return result

def getActionClass(typeName):
    """
    Return a BuildAction class by type name

    Args:
        typeName: A str representing the name of a BuildAction type
    """
    if typeName in BUILDITEM_TYPEMAP:
        actionClass = BUILDITEM_TYPEMAP[typeName]
        if issubclass(actionClass, BuildAction):
            return actionClass

def getBuildItemClass(typeName):
    """
    Return a BuildItem class by type name

    Args:
        typeName: A str representing the name of the BuildItem type
    """
    if typeName in BUILDITEM_TYPEMAP:
        return BUILDITEM_TYPEMAP[typeName]

def getRegisteredActions():
    """
    Return all registered BuildAction classes organized
    by their registered type name
    """
    return {k:v for k,v in BUILDITEM_TYPEMAP.iteritems() if issubclass(v, BuildAction)}

def registerActions(actionClasses):
    """
    Register one or more BuildAction classes

    Args:
        actionClasses: A list of BuildAction classes
    """
    for c in actionClasses:
        typeName = c.getTypeName()
        if typeName == 'group':
            raise ValueError("BuildActions cannot use the reserved type `group`")
        BUILDITEM_TYPEMAP[typeName] = c



class BuildItem(object):
    """
    Represents an action that can be performed during rig building.
    This is a base class not intended for direct use.
    Subclass BuildAction when creating custom rigging operations.
    """

    @staticmethod
    def create(data):
        """
        Create and return a BuildItem based
        on the given serialized data.
        
        This is a factory method that automatically
        determines the instance type from the data.

        Args:
            data: A dict object containing serialized BuildItem data
        """
        itemClass = getBuildItemClass(data['type'])
        if itemClass:
            item = itemClass()
            item.deserialize(data)
            return item

    @classmethod
    def getTypeName(cls):
        """
        Return the type of BuildItem this is.
        Used for factory creation of BuildItems.
        """
        raise NotImplementedError

    def __init__(self):
        self.log = logging.getLogger(self.getLoggerName())

    def getLoggerName(self):
        """
        Return the name of the logger for this BuildItem
        """
        raise NotImplementedError

    def getDisplayName(self):
        """
        Return the display name for this item.
        """
        raise NotImplementedError

    def serialize(self):
        """
        Return this BuildItem as a serialized dict object
        """
        data = {}
        data['type'] = self.getTypeName()
        return data

    def deserialize(self, data):
        """
        Load configuration of this BuildItem from data

        Args:
            data: A dict containing serialized data for this item
        """
        if data['type'] != self.getTypeName():
            raise ValueError('BuildItem type `{0}` does not match data type `{1}`'.format(self.getTypeName(), data['type']))



class BuildGroup(BuildItem):
    """
    Represents a group of BuildItems that will be run in order.
    This enables hierachical structuring of build items.
    """

    @classmethod
    def getTypeName(cls):
        return 'BuildGroup'
    
    def __init__(self):
        super(BuildGroup, self).__init__()
        # the display name of this group
        self.displayName = 'MyBuildGroup'
        # the list of build items to perform in order
        self.children = []

    def getLoggerName(self):
        return 'pulse.buildgroup'

    def getDisplayName(self):
        return self.displayName

    def serialize(self):
        # TODO: make a recursion loop check
        data = super(BuildGroup, self).serialize()
        data['displayName'] = self.displayName
        data['children'] = [c.serialize() for c in self.children]
        return data

    def deserialize(self, data):
        super(BuildGroup, self).deserialize(data)
        self.displayName = data['displayName']
        self.children = [BuildItem.create(c) for c in data['children']]

    def clearChildren(self):
        self.children = []

    def addChild(self, item):
        if item is self:
            raise ValueError('Cannot add BuildGroup as child of itself')
        if not isinstance(item, BuildItem):
            raise ValueError('{0} is not a valid BuildItem type'.format(type(item).__name__))
        self.children.append(item)

    def removeChild(self, item):
        if item in self.children:
            self.children.remove(item)

    def insertChild(self, index, item):
        if not isinstance(item, BuildItem):
            raise ValueError('{0} is not a valid BuildItem type'.format(type(item).__name__))
        self.children.insert(index, item)


BUILDITEM_TYPEMAP['group'] = BuildGroup


class BuildActionError(Exception):
    """
    An error for reporting issues with BuildAction
    configuration or related problems.
    """
    pass


class BuildAction(BuildItem):
    """
    A BuildItem that provides extended functionality.
    This should be used as the base class for all 
    actual rigging operations.
    """

    config = None
    configFile = None

    @classmethod
    def getTypeName(cls):
        result = cls.__name__
        if result.endswith('Action'):
            result = result[:-6]
        return result

    def __init__(self):
        super(BuildAction, self).__init__()
        if self.config is None:
            LOG.warning(self.__class__.__name__ + " was loaded without a config. " +
                "Use pulse action loading methods to ensure BuildActions are loaded properly")
        # initialize attributes from config
        for attr in self.config['attrs']:
            setattr(self, attr['name'], self.getDefaultValue(attr))

    def getLoggerName(self):
        return 'pulse.action.' + self.getTypeName().lower()

    def getDisplayName(self):
        return self.config['displayName']

    def getAttrConfig(self, attrName):
        """
        Return config data for an attribute

        Args:
            attrName: A str name of the attribute
        """
        for attr in self.config['attrs']:
            if attr['name'] == attrName:
                return attr

    def getDefaultValue(self, attr):
        """
        Return the default value for an attribute

        Args:
            attr: A dict object representing the config
                data for the attribute
        """
        if 'value' in attr:
            return attr['value']
        else:
            attrType = attr['type']
            if 'list' in attrType:
                return []
            elif attrType in ['int', 'float']:
                return 0
            elif attrType == 'bool':
                return False

    def serialize(self):
        data = super(BuildAction, self).serialize()
        # serialize values for all attr values
        for attr in self.config['attrs']:
            data[attr['name']] = getattr(self, attr['name'])
        return data

    def deserialize(self, data):
        super(BuildAction, self).deserialize(data)
        # load values for all action attrs
        for attr in self.config['attrs']:
            setattr(self, attr['name'], data[attr['name']])

    def run(self):
        """
        Run this build action. Should be implemented
        in subclasses to perform the rigging operation
        that is desired.
        """
        raise NotImplementedError





class Blueprint(object):
    """
    A Blueprint contains all the information necessary to build
    a full rig.

    It is made up of hierarchical BuildGroups which contained
    ordered lists of BuildSteps that perform the actual rig building.

    It also contains a variety of settings and configurations such
    as the rigs name, build callbacks, etc

    All nodes related to the rig will be referenced by the blueprint,
    and all nodes are organized into rig groups based on the nodes purpose.
    """

    # list of valid node types when adding to a blueprint
    validNodeTypes = (
        pm.nt.Transform,
        pm.nt.Network
    )


    @staticmethod
    def fromData(data):
        result = Blueprint()
        result.deserialize(data)
        return result


    def __init__(self):
        # the name of the rig this blueprint represents
        self.name = 'newRig'
        # the version of this blueprint
        self.version = BLUEPRINT_VERSION
        # the root BuildGroup of this blueprint
        self.rootGroup = BuildGroup()

    def serialize(self):
        data = {}
        data['name'] = self.name
        data['version'] = self.version
        data['buildItems'] = self.rootGroup.serialize()
        return data

    def deserialize(self, data):
        self.name = data['name']
        self.version = data['version']
        self.rootGroup = BuildItem.create(data['buildItems'])




