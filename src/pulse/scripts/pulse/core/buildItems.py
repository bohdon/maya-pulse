
import os
import logging
import re
import pymetanode as meta

from .rigs import RIG_METACLASS

__all__ = [
    'BatchBuildAction',
    'BuildAction',
    'BuildActionError',
    'BuildItem',
    'getActionClass',
    'getBuildItemClass',
    'getRegisteredActions',
    'registerActions',
]


LOG = logging.getLogger(__name__)

BUILDITEM_TYPEMAP = {}


def _incrementName(name):
    numMatch = re.match('(.*?)([0-9]+$)', name)
    if numMatch:
        base, num = numMatch.groups()
        return base + str(int(num) + 1)
    else:
        return name + ' 1'


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
        return 'BuildItem'

    def __init__(self, name=None):
        # the parent BuildItem
        self.itemParent = None
        # the name of this item (unique among siblings)
        self.itemName = None
        # is this item allowed to have children?
        self.itemCanHaveChildren = True
        # list of child BuildItems
        self.itemChildren = []
        # set given or default name
        self.setName(name if name else self.getDefaultName())

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
        return 'pulse.builditem'

    def setName(self, newName):
        if newName:
            self.itemName = newName
        self.ensureUniqueName()

    def getDefaultName(self):
        """
        Return the default name to use when this item has no name
        """
        return 'Build Item'

    def ensureUniqueName(self):
        """
        Change this items name to ensure that
        it is unique among siblings.
        """
        if self.itemParent:
            siblings = [
                c for c in self.itemParent.itemChildren if not (c is self)]
            siblingNames = [s.itemName for s in siblings]
            while self.itemName in siblingNames:
                self.itemName = _incrementName(self.itemName)

    def getDisplayName(self):
        """
        Return the display name for this item.
        """
        if self.itemCanHaveChildren:
            return '{0} ({1})'.format(self.itemName, self.getChildCount())
        else:
            return self.itemName

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

    def getFullPath(self):
        """
        Return the full path to this BuildItem.

        Returns:
            A string path to the item
            e.g. 'MyGroupA/MyGroupB/MyBuildItem'
        """
        parentPath = self.itemParent.getFullPath() if self.itemParent else None
        if parentPath:
            return '{0}/{1}'.format(parentPath, self.itemName)
        else:
            return self.itemName

    def setParent(self, newParent):
        self.itemParent = newParent
        if self.itemParent:
            self.ensureUniqueName()

    def clearChildren(self):
        if not self.itemCanHaveChildren:
            return

        for item in self.itemChildren:
            item.setParent(None)
        self.itemChildren = []

    def addChild(self, item):
        if not self.itemCanHaveChildren:
            return

        if item is self:
            raise ValueError('Cannot add item as child of itself')

        if not isinstance(item, BuildItem):
            raise ValueError(
                '{0} is not a valid BuildItem type'.format(type(item).__name__))

        self.itemChildren.append(item)
        item.setParent(self)

    def removeChild(self, item):
        if not self.itemCanHaveChildren:
            return

        if item in self.itemChildren:
            self.itemChildren.remove(item)
            item.setParent(None)

    def removeChildAt(self, index):
        if not self.itemCanHaveChildren:
            return

        if index < 0 or index >= len(self.itemChildren):
            return

        self.itemChildren[index].setParent(None)
        del self.itemChildren[index]

    def insertChild(self, index, item):
        if not self.itemCanHaveChildren:
            return

        if not isinstance(item, BuildItem):
            raise ValueError(
                '{0} is not a valid BuildItem type'.format(type(item).__name__))

        self.itemChildren.insert(index, item)
        item.setParent(self)

    def getChildCount(self):
        if not self.itemCanHaveChildren:
            return 0

        return len(self.itemChildren)

    def getChildByName(self, name):
        """
        Return a child item by name or path
        """
        if not self.itemCanHaveChildren:
            return

        for item in self.itemChildren:
            if item.itemName == name:
                return item

    def getChildByPath(self, path):
        """
        Return a child item by relative path
        """
        if not self.itemCanHaveChildren:
            return

        if '/' in path:
            childName, grandChildPath = path.split('/', 1)
            child = self.getChildByName(childName)
            if child:
                return child.getChildByPath(grandChildPath)
        else:
            return self.getChildByName(path)

    def childIterator(self):
        """
        Generator that yields this item and all children, recursively.

        Intended for use at build time only.
        """
        yield self

        if self.itemCanHaveChildren:
            for child in self.itemChildren:
                for item in child.childIterator():
                    yield item

    def serialize(self):
        """
        Return this BuildItem as a serialized dict object
        """
        data = {}
        data['type'] = self.getTypeName()
        data['name'] = self.itemName

        if self.itemCanHaveChildren:
            # TODO: make a recursion loop check
            data['children'] = [c.serialize() for c in self.itemChildren]

        return data

    def deserialize(self, data):
        """
        Load configuration of this BuildItem from data

        Args:
            data: A dict containing serialized data for this item
        """
        if data['type'] != self.getTypeName():
            raise ValueError(
                "BuildItem type `{0}` does not match data type `{1}`".format(
                    self.getTypeName(), data['type']))

        self.setName(data['name'])

        if self.itemCanHaveChildren:
            # detach any existing children
            for child in self.itemChildren:
                child.setParent(None)
            # deserialize all children, and connect them to this parent
            self.itemChildren = [BuildItem.create(c) for c in data['children']]
            for child in self.itemChildren:
                if child:
                    # TODO: ensure unique name
                    child.setParent(self)


BUILDITEM_TYPEMAP['BuildItem'] = BuildItem


class BuildActionError(Exception):
    """
    An error for reporting issues with BuildAction
    configuration or related problems.
    """
    pass


class BuildAction(BuildItem):
    """
    The base class for any rigging action that can
    run during a build.

    Both `validate` and `run` must be overridden
    in subclasses to provide functionality when
    checking and building the rig.
    """

    config = None
    configFile = None

    @classmethod
    def getTypeName(cls):
        """
        Return the type name of this BuildAction.
        This is the name of the class without the
        Action suffix.
        """
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

    def __init__(self, name=None, **attrKwargs):
        """
        Args:
            attrKwargs: A dict of default values for this actions attributes.
                Only values corresponding to a valid config attribute are used.
        """
        super(BuildAction, self).__init__(name=name)

        # BuildActions cannot have children
        self.itemCanHaveChildren = False

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
        """
        Return the name of the logger for this BuildItem
        """
        return 'pulse.action.' + self.getTypeName().lower()

    def getDefaultName(self):
        return self.config['displayName']

    def getColor(self):
        """
        Return the color of this BuildItem when represented in the UI
        """
        return self.config.get('color')

    def getIconFile(self):
        """
        Return the full path to this build items icon
        """
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

        Args:
            data: A dict containing meta data to update on the rig
        """
        if not self.rig:
            self.log.error('Cannot update rig meta data, no rig is set')
            return
        meta.updateMetaData(self.rig, RIG_METACLASS, data)

    def validate(self):
        """
        Validate this build action. Should be implemented
        in subclasses to check the action's config data
        and raise BuildActionErrors if anything is invalid.
        """
        raise NotImplementedError

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
    BuildActions can be converted to and from BatchBuildAction,
    but will lose data when converting from a batch action to a
    single action.
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

    def __init__(self, name=None):
        """
        Args:
            actionClass: The BuildAction class this batch action represents
        """
        # declare members before super init to avoid
        # error during default name initialization

        # the BuildAction class this batch represents
        self.actionClass = None

        super(BatchBuildAction, self).__init__(name=name)

        # batch actions cannot have children, even though
        # they will yield actions as if they are children
        self.itemCanHaveChildren = False
        # all constant attribute values
        self.constantValues = {}
        # the list of attribute names that vary per action instance
        self.variantAttributes = []
        # all variant attribute values
        self.variantValues = []

    def getLoggerName(self):
        return 'pulse.batchaction'

    def getDefaultName(self):
        if self.actionClass:
            return self.actionClass.config['displayName']
        else:
            return 'BatchBuildAction'

    def getDisplayName(self):
        if not self.actionClass:
            return '{0} (unconfigured)'.format(self.itemName)
        return '{0} (x{1})'.format(self.itemName, self.getActionCount())

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
        if self.actionClass:
            data['actionClassName'] = self.actionClass.getTypeName()
        else:
            data['actionClassName'] = None
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
            self.setName(self.getDefaultName())

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
                    val = self.actionClass.getDefaultValue(attr)
                    self.constantValues[attr['name']] = val

    def addVariantAttr(self, attrName):
        """
        """
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

    def childIterator(self):
        """
        Generator that yields this item and creates all actions represented
        by the variants of this batch action. The created actions have
        this item set as their parent, so they will have valid paths.

        Intended for use at build time only.
        """
        yield self

        if self.actionClass:
            # build constant value kwargs
            constkwargs = {}
            for k, v in self.constantValues.items():
                if k not in self.variantAttributes:
                    constkwargs[k] = v

            # create and yield new build actions for each variant
            for index, variant in enumerate(self.variantValues):
                kwargs = {
                    'name': '{0}{1}'.format(self.actionClass.getTypeName(), index)
                }
                kwargs.update(constkwargs)
                kwargs.update(variant)
                newAction = self.actionClass(**kwargs)
                yield newAction


BUILDITEM_TYPEMAP['BatchBuildAction'] = BatchBuildAction
