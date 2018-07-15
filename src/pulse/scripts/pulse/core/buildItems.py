
import os
import logging
import re
import pymetanode as meta

from .rigs import RIG_METACLASS

__all__ = [
    'BuildAction',
    'BuildActionData',
    'BuildActionError',
    'BuildActionProxy',
    'BuildActionProxyBatch',
    'BuildItem',
    'BuildStep',
    'getBuildActionClass',
    'getBuildActionConfig',
    'getRegisteredAction',
    'getRegisteredActionIds',
    'getRegisteredActions',
    'registerAction',
]


LOG = logging.getLogger(__name__)

BUILDACTIONMAP = {}


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


def getRegisteredAction(actionId):
    """
    Return a BuildAction config and class by action id

    Args:
        actionId (str): A BuildAction id

    Returns:
        A dict containing {'config':dict, 'class':class}
    """
    if actionId in BUILDACTIONMAP:
        return BUILDACTIONMAP[actionId]


def getBuildActionConfig(actionId):
    """
    Return a BuildAction config by action id

    Args:
        actionId (str): A BuildAction id
    """
    action = getRegisteredAction(actionId)
    if action:
        return action['config']


def _getBuildActionConfigForClass(actionClass):
    """
    Return the config that is associated with a BuildAction class.
    Performs the search by looking for a matching class and returning
    its paired config, instead of looking for the config by id.

    Args:
        actionClass: A BuildAction class
    """
    for v in BUILDACTIONMAP.values():
        if v['class'] is actionClass:
            return v['config']


def getBuildActionClass(actionId):
    """
    Return a BuildAction class by action id

    Args:
        actionId (str): A BuildAction id
    """
    action = getRegisteredAction(actionId)
    if action:
        return action['class']


def getRegisteredActionIds():
    """
    Return all the ids of registered BuildActions
    """
    return BUILDACTIONMAP.keys()


def getRegisteredActions():
    """
    Return all registered BuildAction classes organized by their id

    Returns:
        A dict of {str: {'config': dict, 'class': BuildAction class}}
    """
    return BUILDACTIONMAP.items()


def registerAction(actionConfig, actionClass):
    """
    Register one or more BuildAction classes

    Args:
        actionClass: A BuildAction class
        actionConfig (dict): A config dict for a BuildAction
    """
    action = {
        'config': actionConfig,
        'class': actionClass,
    }
    actionId = actionConfig['id']
    if actionId in BUILDACTIONMAP:
        LOG.error("A BuildAction already exists with id: {0}".format(actionId))
        return

    BUILDACTIONMAP[actionId] = action


def unregisterAction(actionId):
    if actionId in BUILDACTIONMAP:
        del BUILDACTIONMAP[actionId]


class BuildStep(object):
    """
    Represents a step to perform when building a Blueprint.
    Steps are hierarchical, but a BuildStep that performs a BuildAction
    cannot have children.
    """

    # TODO (bsayre): consider adding method to change the action type of the current proxy,
    #       whilst preserving or transferring as much attr data as possible

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

    def __init__(self, name='BuildStep', actionProxy=None, actionId=None):
        # the name of this step (unique among siblings)
        self._name = name
        # the parent BuildStep
        self._parent = None
        # list of child BuildSteps
        self._children = []
        # the BuildActionProxy for this step
        self._actionProxy = actionProxy

        # auto-create a basic BuildActionProxy if an actionId was given
        if actionId:
            self._actionProxy = BuildActionProxy(actionId=actionId)

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
        return self._actionProxy is not None

    @property
    def actionProxy(self):
        return self._actionProxy

    def setActionProxy(self, actionProxy):
        """
        Set a BuildActionProxy for this step. Will fail if
        the step has any children.

        Args:
            actionProxy (BuildActionProxy): The new action proxy
        """
        if self._children:
            LOG.warning("Cannot set a BuildActionProxy on a step with children. "
                        "Clear all children first")
            return

        self._actionProxy = actionProxy

    @property
    def canHaveChildren(self):
        return not self.isAction

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

    def getDisplayName(self):
        """
        Return the display name for this step.
        """
        if self._actionProxy:
            # TODO: use the BuildSteps name somehow to modified the resulting name
            return self._actionProxy.getDisplayName()
        else:
            return '{0} ({1})'.format(self._name, self.getChildCount())

    def getColor(self):
        """
        Return the color of this BuildStep when represented in the UI
        """
        if self._actionProxy:
            return self._actionProxy.getColor()
        else:
            pass

    def getIconFile(self):
        """
        Return the full path to this build step's icon
        """
        if self._actionProxy:
            return self._actionProxy.getIconFile()
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

    def actionGenerator(self):
        if self._actionProxy:
            for elem in self._actionProxy.actionGenerator():
                yield elem

    def serialize(self):
        """
        Return this BuildStep as a serialized dict object
        """
        data = {}
        data['name'] = self._name
        data['action'] = self._actionProxy.serialize()

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
        # TODO: (urgent) need to reconstruct the proper BuildActionProxy class based on data type,
        #       currently this will destroy any batch proxies on load
        actionProxy = BuildActionProxy()
        actionProxy.deserialize(data['action'])
        self.setActionProxy(actionProxy)

        # TODO: warn if throwing away children in a rare case that
        #       both a proxy and children existed (maybe data was manually created).
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


class BuildActionData(object):
    """
    Contains the configuration and data for an action that can be
    performed during a build step.
    """

    def __init__(self, actionId=None):
        self._actionId = actionId
        self.configFile = None
        self._config = None
        self._attrValues = {}

        if self._actionId:
            self.retrieveActionConfig()

    def __repr__(self):
        return "<{0} '{1}'>".format(self.__class__.__name__, self.getActionId())

    @property
    def config(self):
        if self._config is not None:
            return self._config
        return {}

    def hasConfig(self):
        """
        Return True if this object has a valid actionId and
        corresponding config loaded.
        """
        return self._actionId and (self._config is not None)

    def getActionId(self):
        """
        Return the id of the BuildAction
        """
        return self._actionId

    def getShortActionId(self):
        """
        Return the last part of the actions id, after any '.'
        """
        if self._actionId:
            return self._actionId.split('.')[-1]

    def retrieveActionConfig(self):
        self._config = getBuildActionConfig(self._actionId)
        if self._config is None:
            LOG.warning(
                "Failed to find action config for {0}".format(self._actionId))

    def getAttrNames(self):
        """
        Return a list of attribute names for this BuildAction class
        """
        if not self.hasConfig():
            return

        for attr in self.config['attrs']:
            yield attr['name']

    def getAttrConfig(self, attrName):
        """
        Return config data for an attribute

        Args:
            attrName: A str name of the attribute
        """
        if not self.hasConfig():
            return

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
        if not self.hasConfig():
            return

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

    def serialize(self):
        """
        Return this BuildActionData as a serialized dict object
        """
        data = {}
        data['id'] = self._actionId
        if self.hasConfig():
            for attr in self.config['attrs']:
                if attr['name'] in self._attrValues:
                    data[attr['name']] = self._attrValues[attr['name']]
        return data

    def deserialize(self, data):
        """
        Set all values on this BuildActionData from data

        Args:
            data: A dict containing serialized data for this action
        """
        self._actionId = data['id']

        # update config
        if self._actionId:
            self.retrieveActionConfig()

        # load values for all action attrs
        attrs = self.config.get('attrs', [])
        if self.hasConfig():
            for attr in attrs:
                if attr['name'] in data:
                    self._attrValues[attr['name']] = data[attr['name']]
                else:
                    self._attrValues[attr['name']] = self.getDefaultValue(attr)
        elif attrs:
            # TODO: better wording for this warning / issue
            LOG.warning(
                "Failed to load config for action, preserving attr values")
            for k, v in data.items():
                self._attrValues[k] = v


class BuildItem(BuildActionData):
    # TODO: deprecate and remove
    pass


class BuildActionProxy(BuildActionData):
    """
    Acts as a stand-in for a BuildAction during Blueprint editing.
    Contains all attribute values for the configured action, which
    are used to create a real BuildAction at build time.

    This proxy provides a method `actionGenerator` which constructs
    and yields the real BuildAction instances for use a build time.
    Note that multiple BuildActions can come from a single proxy.
    """

    def hasAttrValue(self, name):
        return name in self._attrValues

    def getAttrValue(self, name):
        return self._attrValues[name]

    def setAttrValue(self, name, value):
        self._attrValues[name] = value

    def delAttrValue(self, name):
        del self._attrValues[name]

    def hasActionClass(self):
        return self.getActionId() is not None

    def getDisplayName(self):
        """
        Return the display name of the BuildAction.
        """
        return self.config.get('displayName', self.getShortActionId())

    def getColor(self):
        """
        Return the color of this action when represented in the UI
        """
        return self.config.get('color')

    def getIconFile(self):
        """
        Return the full path to this build items icon
        """
        filename = self.config.get('icon')
        if filename:
            return os.path.join(os.path.dirname(self.configFile), filename)

    def actionGenerator(self):
        """
        Generator that yields a BuildAction for every action that this
        proxy represents.
        """
        if self.hasActionClass():
            yield BuildAction.fromData(self.serialize())


class BuildActionProxyBatch(BuildActionProxy):
    """
    A BuildActionProxy that generates multiple BuildActions
    which will be run in order, and can have different values for
    one or more attributes.

    Provides functionality for converting to and from a BuildActionProxy,
    but note that data will be lost when converting from a batch action to a
    single action (since variant attribute values will be discarded).
    """

    @staticmethod
    def fromAction(action):
        """
        Return a new BatchBuildAction using a BuildAction as reference

        Args:
            action: A BuildAction object
        """
        batch = BuildActionProxyBatch()
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
        super(BuildActionProxyBatch, self).__init__()

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
        data = super(BuildActionProxyBatch, self).serialize()
        if self.actionClass:
            data['actionClassName'] = self.actionClass.getTypeName()
        else:
            data['actionClassName'] = None
        data['constantValues'] = self.constantValues
        data['variantAttributes'] = self.variantAttributes
        data['variantValues'] = self.variantValues
        return data

    def deserialize(self, data):
        super(BuildActionProxyBatch, self).deserialize(data)
        # retrieve action class
        actionClassName = data['actionClassName']
        if actionClassName:
            self.setActionClass(getBuildActionClass(actionClassName))
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
        as members on this BuildActionProxyBatch

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


class BatchBuildAction(BuildActionProxyBatch):
    # TODO: deprecate and remove
    pass


class BuildAction(BuildActionData):
    """
    The base class for any rigging action that can run during a build.

    Both `validate` and `run` must be overridden in subclasses to
    provide functionality when checking and building the rig.
    """

    @staticmethod
    def fromActionId(actionId):
        """
        Create and return a BuildAction by class actionId.

        Args:
            actionId (str): A BuildAction id.
        """
        actionClass = getBuildActionClass(actionId)
        if actionClass:
            item = actionClass()
            return item
        else:
            LOG.error("Failed to find BuildAction class: {0}".format(actionId))

    @staticmethod
    def fromData(data):
        """
        Create and return a BuildAction based on the given serialized data.

        This is a factory method that automatically determines
        the class to instance using the action id in the data.

        Args:
            data: A dict object containing serialized BuildAction data
        """
        actionClass = getBuildActionClass(data['id'])
        if actionClass:
            item = actionClass()
            item.deserialize(data)
            return item
        else:
            LOG.error(
                "Failed to find BuildAction class: {0}".format(data['id']))

    @staticmethod
    def fromBatchAction(batchAction):
        """
        Return a new BuildAction created using a BuildActionProxyBatch
        as reference.
        """
        # TODO: move to proxies
        if not batchAction.actionClass:
            raise ValueError(
                "BuildActionProxyBatch must have a valid actionClass")

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

        # logger is initialized the first time its accessed
        self._log = None
        # rig is only available during build
        self.rig = None

        # pull action name from the class name
        self._config = _getBuildActionConfigForClass(self.__class__)
        if self._config:
            self._actionId = self.config['id']
        else:
            LOG.warning("Constructed an unregistered BuildAction: {0}, "
                        "cannot retrieve config".format(self.__class__.__name__))
            return

        # initialize attributes from config
        for attr in self.config['attrs']:
            if not hasattr(self, attr['name']):
                if attr['name'] in attrKwargs:
                    setattr(self, attr['name'], attrKwargs[attr['name']])
                else:
                    setattr(self, attr['name'], self.getDefaultValue(attr))

    def __repr__(self):
        return "<{0}>".format(self.__class__.__name__)
    
    def __getattr__(self, name):
        if name in self._attrValues:
            return self._attrValues[name]
        raise AttributeError

    def retrieveActionConfig(self):
        # do nothing. BuildAction classes automatically retrieve
        # their config on init using the class itself to lookup
        # a registered config.
        pass

    def getLoggerName(self):
        """
        Return the name of the logger for this BuildAction
        """
        return 'pulse.action.' + self.getActionId()

    @property
    def log(self):
        if not self._log:
            self._log = logging.getLogger(self.getLoggerName())
        return self._log

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
