
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
    'BuildStep',
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


class BuildStep(object):
    """
    Represents a step to perform when building a Blueprint.
    Steps are hierarchical, but a BuildStep that performs a BuildAction
    cannot have children.
    """

    @staticmethod
    def fromData(data):
        """
        Return a new BuildStep instance created
        from serialized data.

        Args:
            data (dict): Serialized BuildStep data
        """
        step = BuildStep()
        step.deserialize(data)
        return step

    @staticmethod
    def fromActionClass(actionClass):
        """
        Return a new BuildStep that represents a
        new BuildAction of a specific class.

        Args:
            actionClass (str): The name of the BuildAction class
        """
        step = BuildStep()
        step.setIsAction(True)
        step.setActionClass(actionClass)
        return step

    @staticmethod
    def fromAction(action):
        """
        Return a new BuildStep for an existing BuildAction instance.

        Args:
            action (BuildAction): A BuildAction. Should not already be
                in use by another BuildStep, otherwise this may lead to
                unpredictable behavior.
        """
        step = BuildStep(action.getDisplayName())
        step.setIsAction(True)
        step.setAction(action)
        return step

    def __init__(self, name='BuildStep'):
        # the name of this step (unique among siblings)
        self._name = name
        # does this step represent a BuildAction?
        self._isAction = False
        # the name of the BuildAction class for this step
        self._actionClass = None
        # the BuildAction for this step, created
        # automatically when the action class is set
        self._action = None
        # the parent BuildStep
        self._parent = None
        # list of child BuildSteps
        self._children = []

    @property
    def name(self):
        return self._name

    def setName(self, newName):
        """
        Set the name of the BuildStep, modifying it if necessary
        to ensure that it is unique among siblings.

        Args:
            newName (str): The new name of the step
        """
        if newName:
            self._name = newName
        self.ensureUniqueName()

    @property
    def isAction(self):
        return self._isAction

    def setIsAction(self, newIsAction):
        """
        Set whether or not this step represents a BuildAction.
        If true, will clear all children. If False, will clear
        any existing action.

        Args:
            newIsAction (bool): The new value for isAction
        """
        if self._isAction != newIsAction:
            self._isAction = newIsAction
            if not self._isAction:
                self._actionClass = None
                self._action = None

    @property
    def canHaveChildren(self):
        return not self.isAction

    @property
    def actionClass(self):
        return self._actionClass

    @property
    def action(self):
        return self._action

    def setAction(self, action):
        """
        Set the BuildStep's action, and set the actionClass to match.

        Args:
            action (BuildAction): A BuildAction instance. Should not
                be in use by another BuildStep.
        """
        if not self.isAction:
            raise RuntimeError(
                'BuildStep is not an action, set isAction to True first')

        if not isinstance(action, BuildAction):
            raise TypeError(
                'Expected BuildAction, got {0}'.format(type(action).__name__))

        self._actionClass = action.getTypeName()
        self._action = action

    @property
    def parent(self):
        return self._parent

    def setParent(self, newParent):
        if newParent and not newParent.canHaveChildren:
            return

        if self._parent is not newParent:
            self._parent = newParent
            if self._parent:
                self.ensureUniqueName()

    @property
    def children(self):
        return self._children

    def __repr__(self):
        return "<BuildStep '{0}'>".format(self.getDisplayName())

    def ensureUniqueName(self):
        """
        Change this step's name to ensure that
        it is unique among siblings.
        """
        if self._parent:
            siblings = [c for c in self._parent.children if not (c is self)]
            siblingNames = [s.name for s in siblings]
            while self._name in siblingNames:
                self._name = _incrementName(self._name)

    def setActionClass(self, name):
        """
        Set the BuildAction class for this step by name.
        Rebuilds the BuildAction instance, but attempts to
        preserve data from the previous action if applicable.

        Args:
            name (str): The name of a BuildAction class
        """
        if not self.isAction:
            return

        if self._actionClass != name:
            self._actionClass = name
            self.rebuildAction()

    def rebuildAction(self, preserveData=True):
        """
        Rebuild the current BuildAction instance for this step
        based on the current action class.

        Args:
            preserveData (bool): When true, data will be transferred
                from the existing BuildAction, if one exists.
        """
        if not self.isAction:
            self._actionClass = None
            self._action = None
            return

        if not self._actionClass:
            self._action = None
            return

        oldAction = self._action
        self._action = BuildAction.fromTypeName(self._actionClass)

        if preserveData:
            if oldAction and self._action:
                self._action.deserialize(oldAction)

        # TODO: set name to match new action?

    def getDisplayName(self):
        """
        Return the display name for this step.
        """
        if self.isAction:
            # TODO: allow BuildAction to modify display name
            #       based on its current state
            return self._name
        else:
            return '{0} ({1})'.format(self._name, self.getChildCount())

    def getColor(self):
        """
        Return the color of this BuildStep when represented in the UI
        """
        if self.isAction and self._action:
            return self._action.getColor()
        else:
            pass

    def getIconFile(self):
        """
        Return the full path to this build step's icon
        """
        if self.isAction and self._action:
            return self._action.getIconFile()
        else:
            pass

    def getFullPath(self):
        """
        Return the full path to this BuildStep.

        Returns:
            A string path to the step
            e.g. 'MyGroupA/MyGroupB/MyBuildStep'
        """
        if self._parent:
            parentPath = self._parent.getFullPath()
            if parentPath:
                return '{0}/{1}'.format(parentPath, self._name)
            else:
                return self._name
        else:
            # a root step, or step without a parent has no path
            return None

    def clearChildren(self):
        if not self.canHaveChildren:
            return

        for step in self._children:
            step.setParent(None)

        self._children = []

    def addChild(self, step):
        if not self.canHaveChildren:
            return

        if step is self:
            raise ValueError('Cannot add step as child of itself')

        if not isinstance(step, BuildStep):
            raise TypeError(
                'Expected BuildStep, got {0}'.format(type(step).__name__))

        self._children.append(step)
        step.setParent(self)

    def removeChild(self, step):
        if not self.canHaveChildren:
            return

        if step in self._children:
            self._children.remove(step)
            step.setParent(None)

    def removeChildAt(self, index):
        if not self.canHaveChildren:
            return

        if index < 0 or index >= len(self._children):
            return

        self._children[index].setParent(None)
        del self._children[index]

    def insertChild(self, index, step):
        if not self.canHaveChildren:
            return

        if not isinstance(step, BuildStep):
            raise TypeError(
                'Expected BuildStep, got {0}'.format(type(step).__name__))

        self._children.insert(index, step)
        step.setParent(self)

    def getChildCount(self):
        if not self.canHaveChildren:
            return 0

        return len(self._children)

    def getChildByName(self, name):
        """
        Return a child step by name
        """
        if not self.canHaveChildren:
            return

        for step in self._children:
            if step.name == name:
                return step

    def getChildByPath(self, path):
        """
        Return a child step by relative path
        """
        if not self.canHaveChildren:
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
        Generator that yields this step and all children, recursively.
        """
        yield self

        if self.canHaveChildren:
            for child in self._children:
                for step in child.childIterator():
                    yield step

    def serialize(self):
        """
        Return this BuildStep as a serialized dict object
        """
        data = {}
        data['name'] = self._name
        data['isAction'] = self._isAction
        if self.isAction:
            data['actionClass'] = self._actionClass
            if self._action:
                data['action'] = self._action.serialize()

        if self.canHaveChildren:
            # TODO: perform a recursion loop check
            data['children'] = [c.serialize() for c in self._children]

        return data

    def deserialize(self, data):
        """
        Load configuration of this BuildStep from data

        Args:
            data: A dict containing serialized data for this step
        """
        self.setName(data['name'])
        self.setIsAction(data['isAction'])
        if 'actionClass' in data:
            self.setActionClass(data['actionClass'])
        if 'action' in data and self._action:
            self._action.deserialize(data['action'])

        if self.canHaveChildren:
            # detach any existing children
            self.clearChildren()
            # deserialize all children, and connect them to this parent
            self._children = [BuildStep.fromData(c) for c in data['children']]
            for child in self._children:
                if child:
                    child.setParent(self)


class BuildActionError(Exception):
    """
    A BuildAction was misconfigured or failed during build
    """
    pass


class BuildItem(object):
    """
    Represents an action that can be performed during a build step.
    This is a base class not intended for direct use.
    Subclass BuildAction when creating custom rigging operations.
    """

    @staticmethod
    def fromTypeName(name):
        """
        Create and return a BuildItem by type name.

        Args:
            name (str): The name of a registered BuildItem class
        """
        itemClass = getBuildItemClass(name)
        if itemClass:
            item = itemClass()
            return item
        else:
            LOG.error("Failed to find BuildItemClass "
                      "for data type: {0}".format(name))

    @staticmethod
    def create(data):
        """
        Create and return a BuildItem based
        on the given serialized data.

        This is a factory method that automatically
        determines the class to instance from the data type.

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

    def __init__(self):
        pass

    def __repr__(self):
        return "<{0}>".format(self.__class__.__name__)

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

    def getDefaultName(self):
        """
        Return the default name to use when this item has no name
        """
        return 'Build Item'

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
            raise ValueError(
                "BuildItem type `{0}` does not match data type `{1}`".format(
                    self.getTypeName(), data['type']))


BUILDITEM_TYPEMAP['BuildItem'] = BuildItem


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
    def getDisplayName(self):
        """
        Return the display name of the BuildAction.
        """
        return self.config['displayName']

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

    # TODO: BatchBuildAction should no longer be a BuildItem,
    #       but instead be part of BuildStep so that it can expand
    #       during BuildAction iteration

    @classmethod
    def getTypeName(cls):
        return 'BatchBuildAction'

    @classmethod
    def getDisplayName(self):
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
