
import os
import logging
import pymetanode as meta

from .rigs import RIG_METACLASS

__all__ = [
    'BatchBuildAction',
    'BuildAction',
    'BuildActionError',
    'BuildGroup',
    'BuildItem',
    'getActionClass',
    'getBuildItemClass',
    'getRegisteredActions',
    'registerActions',
]


LOG = logging.getLogger(__name__)

BUILDITEM_TYPEMAP = {}


def _copyData(data, refNode=None):
    """
    Performs a deep copy of the given data using pymetanode to
    encode and decode the values.
    """
    return meta.decodeMetaData(meta.encodeMetaData(data), refNode)


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

    Returns:
        A dict of {string: BuildAction} where keys represent
        the registered type name of the action.
    """
    return {k: v for k, v in BUILDITEM_TYPEMAP.iteritems() if issubclass(v, BuildAction)}


def registerActions(actionClasses):
    """
    Register one or more BuildAction classes

    Args:
        actionClasses: A list of BuildAction classes
    """
    for c in actionClasses:
        typeName = c.getTypeName()
        if typeName == 'group':
            raise ValueError(
                "BuildActions cannot use the reserved type `group`")
        elif typeName in BUILDITEM_TYPEMAP:
            if BUILDITEM_TYPEMAP[typeName].config.get('isBuiltin', False):
                LOG.error("A built-in BuildAction already "
                          "exists with type name: {0}".format(typeName))
                continue
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
        else:
            LOG.error("Failed to find BuildItemClass "
                        "for data type: {0}".format(data['type']))

    @classmethod
    def getTypeName(cls):
        """
        Return the type of BuildItem this is.
        Used for factory creation of BuildItems.
        """
        raise NotImplementedError

    def __init__(self):
        self.parent = None

    def __repr__(self):
        return "<{0} '{1}'>".format(self.__class__.__name__, self.getDisplayName())

    @property
    def log(self):
        if not hasattr(self, 'log'):
            self._log = logging.getLogger(self.getLoggerName())
        return self._log

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

    def getColor(self):
        """
        Return the color of this BuildItem when represented in the UI
        """
        pass

    def getIconFile(self):
        """
        Return the full path to this build items icon
        """
        pass

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
            raise ValueError('BuildItem type `{0}` does not match data type `{1}`'.format(
                self.getTypeName(), data['type']))


class BuildGroup(BuildItem):
    """
    Represents a group of BuildItems that will be run in order.
    This enables hierachical structuring of build items.
    """

    @classmethod
    def getTypeName(cls):
        return 'BuildGroup'

    def __init__(self, displayName='NewGroup'):
        super(BuildGroup, self).__init__()
        # the display name of this group
        self.displayName = displayName
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
        for item in self.children:
            if item:
                item.parent = self

    def clearChildren(self):
        for item in self.children:
            item.parent = None
        self.children = []

    def addChild(self, item):
        if item is self:
            raise ValueError('Cannot add BuildGroup as child of itself')
        if not isinstance(item, BuildItem):
            raise ValueError(
                '{0} is not a valid BuildItem type'.format(type(item).__name__))
        self.children.append(item)
        item.parent = self

    def removeChild(self, item):
        if item in self.children:
            self.children.remove(item)
            item.parent = None

    def removeChildAt(self, index):
        if index < 0 or index >= len(self.children):
            return

        self.children[index].parent = None
        del self.children[index]

    def insertChild(self, index, item):
        if not isinstance(item, BuildItem):
            raise ValueError(
                '{0} is not a valid BuildItem type'.format(type(item).__name__))
        self.children.insert(index, item)
        item.parent = self

    def getChildCount(self):
        return len(self.children)

    def getChildGroupByName(self, name):
        """
        Return a child BuildGroup by name
        """
        for item in self.children:
            if isinstance(item, BuildGroup) and item.displayName == name:
                return item

    def actionIterator(self, parentPath=None):
        """
        Yields all BuildActions in this BuildGroup,
        recursively handling child BuildGroups as well.

        Args:
            parentPath: A string path representing the parent BuildGroup

        Returns:
            Iterator of (BuildAction, string) representing all actions and
            the build group path leading to them.
        """
        thisPath = '/'.join([parentPath, self.getDisplayName()]
                            ) if parentPath else self.getDisplayName()
        for index, child in enumerate(self.children):
            if thisPath:
                pathAtIndex = '{0}[{1}]'.format(thisPath, index)
            else:
                pathAtIndex = None
            if isinstance(child, (BuildGroup, BatchBuildAction)):
                # iterate through child group or batch actions
                for subItem, subPath in child.actionIterator(pathAtIndex):
                    yield subItem, subPath
            elif isinstance(child, BuildAction):
                # return the action
                yield child, pathAtIndex


BUILDITEM_TYPEMAP['BuildGroup'] = BuildGroup


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

    @classmethod
    def getAttrNames(cls):
        """
        Return a list of attribute names for this BuildAction class
        """
        for attr in cls.config['attrs']:
            yield attr['name']

    @classmethod
    def getAttrConfig(cls, attrName):
        """
        Return config data for an attribute

        Args:
            attrName: A str name of the attribute
        """
        for attr in cls.config['attrs']:
            if attr['name'] == attrName:
                return attr

    @classmethod
    def getDefaultValue(cls, attr):
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
            elif attrType == 'bool':
                return False
            elif attrType in ['int', 'float']:
                return 0
            elif attrType == 'string':
                return ''

    @staticmethod
    def fromBatchAction(batchAction):
        """
        Return a new BuildAction created using a BatchBuildAction
        as reference.
        """
        if not batchAction.actionClass:
            raise ValueError("BatchBuildAction must have a valid actionClass")

        # copy attribute values
        data = batchAction.constantValues
        if batchAction.variantValues:
            data.update(batchAction.variantValues[0])
        data = _copyData(data)

        return batchAction.actionClass(**data)

    def __init__(self, **attrKwargs):
        """
        Args:
            attrKwargs: A dict of default values for this actions attributes.
                Only values corresponding to a valid config attribute are used.
        """
        super(BuildAction, self).__init__()
        if self.config is None:
            LOG.warning(self.__class__.__name__ + " was loaded without a config. " +
                        "Use pulse action loading methods to ensure BuildActions are loaded properly")
        # rig is only available during build
        self.rig = None
        # initialize attributes from config
        for attr in self.config['attrs']:
            if not hasattr(self, attr['name']):
                if attr['name'] in attrKwargs:
                    setattr(self, attr['name'], attrKwargs[attr['name']])
                else:
                    setattr(self, attr['name'], self.getDefaultValue(attr))

    def getLoggerName(self):
        return 'pulse.action.' + self.getTypeName().lower()

    def getDisplayName(self):
        return self.config['displayName']

    def getColor(self):
        return self.config.get('color')

    def getIconFile(self):
        filename = self.config.get('icon')
        if filename:
            return os.path.join(os.path.dirname(self.configFile), filename)

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
            if attr['name'] in data:
                setattr(self, attr['name'], data[attr['name']])
            else:
                self.log.warning(
                    'No serialized data for attribute: {0}'.format(attr['name']))
                setattr(self, attr['name'], self.getDefaultValue(attr))

    def getRigMetaData(self):
        """
        Return all meta data on the rig being built
        """
        if not self.rig:
            self.log.error('Cannot get rig meta data, no rig is set')
            return
        return meta.getMetaData(self.rig, RIG_METACLASS)

    def updateRigMetaData(self, data):
        """
        Add some meta data to the rig being built
        """
        if not self.rig:
            self.log.error('Cannot update rig meta data, no rig is set')
            return
        meta.updateMetaData(self.rig, RIG_METACLASS, data)

    def run(self):
        """
        Run this build action. Should be implemented
        in subclasses to perform the rigging operation
        that is desired.
        """
        raise NotImplementedError


class BatchBuildAction(BuildItem):
    """
    A special BuildItem that is designed to behave like
    an existing BuildAction, but allows running the action
    multiple times with different values for a subset of attributes.
    BuildActions can be converted to and from BatchBuildAction
    (with data loss when converting from Batch) for convenience.

    BatchBuildActions are not run, instead they provide an actionIterator
    just like BuildGroups which generates BuildAction instances at build time.
    """

    @classmethod
    def getTypeName(cls):
        return 'BatchBuildAction'

    @staticmethod
    def fromAction(action):
        """
        Return a new BatchBuildAction using a BuildAction as reference

        Args:
            action: A BuildAction object
        """
        batch = BatchBuildAction()
        batch.setActionClass(action.__class__)

        # copy attribute values
        attrNames = list(action.getAttrNames())
        data = {k: v for k, v in action.__dict__.iteritems() if k in attrNames}
        batch.constantValues = _copyData(data)
        return batch

    def __init__(self):
        """
        Args:
            actionClass: The BuildAction class this batch action represents
        """
        super(BatchBuildAction, self).__init__()
        # the BuildAction class this batch represents
        self.actionClass = None
        # all constant attribute values
        self.constantValues = {}
        # the list of attribute names that vary per action instance
        self.variantAttributes = []
        # all variant attribute values
        self.variantValues = []

    def getLoggerName(self):
        return 'pulse.batchaction'

    def getDisplayName(self):
        if not self.actionClass:
            return 'BatchBuildAction (unconfigured)'

        return self.actionClass.config['displayName']

    def getColor(self):
        if self.actionClass:
            return self.actionClass.config.get('color')

    def getIconFile(self):
        if self.actionClass:
            filename = self.actionClass.config.get('icon')
            if filename:
                return os.path.join(os.path.dirname(self.actionClass.configFile), filename)

    def serialize(self):
        data = super(BatchBuildAction, self).serialize()
        data['actionClassName'] = self.actionClass.getTypeName(
        ) if self.actionClass else None
        data['constantValues'] = self.constantValues
        data['variantAttributes'] = self.variantAttributes
        data['variantValues'] = self.variantValues
        return data

    def deserialize(self, data):
        super(BatchBuildAction, self).deserialize(data)
        # retrieve action class
        actionClassName = data['actionClassName']
        if actionClassName:
            self.setActionClass(getActionClass(actionClassName))
        else:
            self.setActionClass(None)
        # all attributes values
        self.constantValues = data['constantValues']
        self.variantAttributes = data['variantAttributes']
        self.variantValues = data['variantValues']

    def setActionClass(self, actionClass):
        """
        Configure this batch action to represent the given BuildAction class.
        Causes attribute values and variants to be cleared.

        Args:
            actionClass: A BuildAction class
        """
        if self.actionClass == actionClass:
            return

        self.actionClass = actionClass
        self.constantValues = {}
        self.variantAttributes = []
        self.variantValues = []

        if self.actionClass:
            # initialize attributes from config
            self._initActionAttrs()

    def _initActionAttrs(self):
        """
        Initialize all attributes for a BuildAction class
        as members on this BatchBuildAction

        Args:
            actionClass: A BuildAction class
        """
        if self.actionClass:
            for attr in self.actionClass.config['attrs']:
                if attr['name'] not in self.constantValues:
                    self.constantValues[attr['name']
                                        ] = self.actionClass.getDefaultValue(attr)

    def addVariantAttr(self, attrName):
        if attrName in self.variantAttributes:
            return

        # add attr to variant attrs list
        self.variantAttributes.append(attrName)
        # update variant values with new attr, using
        # current constant value for all variants
        for item in self.variantValues:
            if attrName not in item:
                item[attrName] = self.constantValues[attrName]
        # remove attribute from constant values
        del self.constantValues[attrName]

    def removeVariantAttr(self, attrName):
        """
        """
        if attrName not in self.variantAttributes:
            return

        # remove from attributes list
        self.variantAttributes.remove(attrName)
        # add to constant values, using either first variant
        # value or the default
        if len(self.variantValues):
            self.constantValues[attrName] = self.variantValues[0][attrName]
        else:
            attr = self.actionClass.getAttrConfig(attrName)
            self.constantValues[attrName] = self.actionClass.getDefaultValue(
                attr)
        # remove all values from variant values
        for item in self.variantValues:
            del item[attrName]

    def _createNewVariant(self):
        variant = {}
        for attrName in self.variantAttributes:
            attr = self.actionClass.getAttrConfig(attrName)
            variant[attrName] = self.actionClass.getDefaultValue(attr)
        return variant

    def addVariant(self):
        """
        Add a variant of attribute values.
        """
        self.variantValues.append(self._createNewVariant())

    def insertVariant(self, position):
        """
        Insert a variant of attribute values.
        """
        self.variantValues.insert(position, self._createNewVariant())

    def removeVariantAt(self, position):
        """
        Remove a variant of attribute values.
        """
        count = len(self.variantValues)
        if position >= -count and position < count:
            del self.variantValues[position]

    def getActionCount(self):
        """
        Return how many action attribute variants this batch contains
        """
        return len(self.variantValues)

    def actionIterator(self, parentPath=None):
        """
        Return an iterator for all action instances that this batch
        action represents, with their appropriate attribuate variations.

        Args:
            parentPath: A string path representing the parent BuildGroup

        Returns:
            Iterator of (BuildAction, string) representing all actions and
            the build group path leading to them.
        """
        _parentPath = (parentPath + '/') if parentPath else ''
        thisPath = _parentPath + 'Batch'
        for index, variant in enumerate(self.variantValues):
            pathAtIndex = '{0}[{1}]'.format(thisPath, index)
            kwargs = {k: v for k, v in self.constantValues.iteritems(
            ) if k not in self.variantAttributes}
            kwargs.update(variant)
            yield self.actionClass(**kwargs), pathAtIndex


BUILDITEM_TYPEMAP['BatchBuildAction'] = BatchBuildAction
