
import os
import logging
import re
import pymetanode as meta

from .rigs import RIG_METACLASS
from .serializer import UnsortableOrderedDict

__all__ = [
    'BuildAction',
    'BuildActionData',
    'BuildActionError',
    'BuildActionProxy',
    'BuildStep',
    'getBuildActionClass',
    'getBuildActionConfig',
    'getRegisteredAction',
    'getRegisteredActionConfigs',
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
    Return all registered BuildAction configs and classes organized by their id

    Returns:
        A dict of {str: {'config': dict, 'class': BuildAction class}}
    """
    return {k: v for k, v in BUILDACTIONMAP}


def getRegisteredActionConfigs():
    """
    Return all registered BuildAction configs

    Returns:
        A dict of {str: {'config': dict, 'class': BuildAction class}}
    """
    return [i['config'] for i in BUILDACTIONMAP.values()]


def registerAction(actionConfig, actionClass):
    """
    Register one or more BuildAction classes

    Args:
        actionClass: A BuildAction class
        actionConfig (dict): A config dict for a BuildAction
    """
    # TODO: prevent registration of invalid configs
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
        newStep = BuildStep()
        newStep.deserialize(data)
        return newStep

    def __init__(self, name=None, actionProxy=None, actionId=None):
        # the name of this step (unique among siblings)
        self._name = None
        # the parent BuildStep
        self._parent = None
        # list of child BuildSteps
        self._children = []
        # the BuildActionProxy for this step
        self._actionProxy = actionProxy

        # auto-create a basic BuildActionProxy if an actionId was given
        if actionId:
            self._actionProxy = BuildActionProxy(actionId)

        # set the name, potentially defaulting to the action's name
        self.setName(name)

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
        # ensure a non-null name
        if not newName:
            if self._actionProxy:
                newName = self._actionProxy.getDisplayName()
            else:
                newName = 'New Step'
        # strip name and ensure its unique among siblings
        newNameClean = newName.strip()
        if self._name != newNameClean:
            self._name = newNameClean
            self.ensureUniqueName()

    def setNameFromAction(self):
        """
        Set the name of the BuildStep to match the action it contains.
        """
        if self._actionProxy:
            self.setName(self._actionProxy.getDisplayName())

    def isAction(self):
        return self._actionProxy is not None

    @property
    def actionProxy(self):
        return self._actionProxy

    def setActionProxy(self, actionProxy, updateName=True):
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
        if updateName and self._actionProxy:
            self._name = self._actionProxy.getDisplayName()
            self.ensureUniqueName()

    @property
    def canHaveChildren(self):
        return not self.isAction()

    @property
    def parent(self):
        return self._parent

    def setParentInternal(self, newParent):
        self._parent = newParent
        self.onParentChanged()

    def setParent(self, newParent):
        """
        Set the parent of this BuildStep, removing it from
        its old parent if necessary.
        """
        if newParent and not newParent.canHaveChildren:
            raise ValueError(
                "Cannot set parent to step that cannot have children: {0}".format(newParent))

        if self._parent is not newParent:
            if self._parent:
                self._parent.removeChildInternal(self)
                self._parent = None
            if newParent:
                newParent.addChild(self)
            else:
                self.setParentInternal(None)

    def onParentChanged(self):
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
            if self._actionProxy.isVariantAction():
                return '{0} (x{1})'.format(
                    self._name, self._actionProxy.numVariants())
            else:
                return '{0}'.format(self._name)
        else:
            return '{0} ({1})'.format(self._name, self.numChildren())

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

    def indexInParent(self):
        """
        Return the index of this within its parent's list of children.
        """
        if self.parent:
            return self.parent.getChildIndex(self)
        else:
            return 0

    def clearChildren(self):
        if not self.canHaveChildren:
            return

        for step in self._children:
            step.setParentInternal(None)

        self._children = []

    def addChild(self, step):
        if not self.canHaveChildren:
            return

        if step is self:
            raise ValueError('Cannot add step as child of itself')

        if not isinstance(step, BuildStep):
            raise TypeError(
                'Expected BuildStep, got {0}'.format(type(step).__name__))

        if step not in self._children:
            self._children.append(step)
            step.setParentInternal(self)

    def addChildren(self, steps):
        for step in steps:
            self.addChild(step)

    def removeChild(self, step):
        if not self.canHaveChildren:
            return

        if step in self._children:
            self._children.remove(step)
            step.setParentInternal(None)

    def removeChildInternal(self, step):
        if step in self._children:
            self._children.remove(step)

    def removeChildren(self, index, count):
        for _ in range(count):
            self.removeChildAt(index)

    def removeChildAt(self, index):
        if not self.canHaveChildren:
            return

        if index < 0 or index >= len(self._children):
            return

        step = self._children[index]
        step.setParentInternal(None)

        del self._children[index]

    def removeFromParent(self):
        """
        Remove this item from its parent, if any.
        """
        if self.parent:
            self.parent.removeChild(self)

    def insertChild(self, index, step):
        if not self.canHaveChildren:
            return

        if not isinstance(step, BuildStep):
            raise TypeError(
                'Expected BuildStep, got {0}'.format(type(step).__name__))

        if step not in self._children:
            self._children.insert(index, step)
            step.setParentInternal(self)

    def numChildren(self):
        if not self.canHaveChildren:
            return 0

        return len(self._children)

    def hasAnyChildren(self):
        return self.numChildren() != 0

    def hasParent(self, step):
        """
        Return True if the step is an immediate or distance parent of this step.
        """
        if self.parent:
            if self.parent == step:
                return True
            else:
                return self.parent.hasParent(step)
        return False

    def getChildAt(self, index):
        if not self.canHaveChildren:
            return

        if index < 0 or index >= len(self._children):
            LOG.error("child index out of range: {0}, num children: {1}".format(
                index, len(self._children)))
            return

        return self._children[index]

    def getChildIndex(self, step):
        """
        Return the index of a BuildStep within this step's list of children
        """
        if not self.canHaveChildren:
            return -1

        return self._children.index(step)

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

    def actionIterator(self):
        if self._actionProxy:
            for elem in self._actionProxy.actionIterator():
                yield elem

    def serialize(self):
        """
        Return this BuildStep as a serialized dict object
        """
        data = UnsortableOrderedDict()
        data['name'] = self._name
        if self._actionProxy:
            data['action'] = self._actionProxy.serialize()

        if self.numChildren() > 0:
            # TODO: perform a recursion loop check
            data['children'] = [c.serialize() for c in self._children]

        return data

    def deserialize(self, data):
        """
        Load configuration of this BuildStep from data

        Args:
            data: A dict containing serialized data for this step
        """
        self.setName(data.get('name', None))
        if 'action' in data:
            newActionProxy = BuildActionProxy()
            newActionProxy.deserialize(data['action'])
            self.setActionProxy(newActionProxy, updateName=False)
        else:
            self._actionProxy = None

        # TODO: warn if throwing away children in a rare case that
        #       both a proxy and children existed (maybe data was manually created).
        if self.canHaveChildren:
            # detach any existing children
            self.clearChildren()
            # deserialize all children, and connect them to this parent
            self._children = [BuildStep.fromData(
                c) for c in data.get('children', [])]
            for child in self._children:
                if child:
                    child.setParent(self)

    @staticmethod
    def getTopmostSteps(steps):
        """
        Return a copy of the list of BuildSteps that doesn't include
        any BuildSteps that have a parent or distant parent in the list.
        """
        def hasAnyParent(step, parents):
            for parent in parents:
                if step != parent and step.hasParent(parent):
                    return True
            return False

        topSteps = []

        for step in steps:
            if not hasAnyParent(step, steps):
                topSteps.append(step)

        return topSteps


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

    def isActionIdValid(self):
        return self._actionId is not None

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
        """
        Get the config for the current actionId and store it on this data
        """
        self._config = getBuildActionConfig(self._actionId)
        if self._config is None:
            LOG.warning(
                "Failed to find action config for {0}".format(self._actionId))

    def numAttrs(self):
        """
        Return the number of attributes that this BuildAction has
        """
        return len(self.getAttrs())

    def getAttrs(self):
        """
        Return all attrs for this BuildAction class

        Returns:
            A list of dict representing all attr configs
        """
        return self.config['attrs']

    def getAttrNames(self):
        """
        Return a list of attribute names for this BuildAction class
        """
        if not self.hasConfig():
            return

        for attr in self.config['attrs']:
            yield attr['name']

    def hasAttrConfig(self, attrName):
        """
        Return True if this action's config contains the attribute.
        """
        return self.getAttrConfig(attrName) is not None

    def hasAttr(self, attrName):
        """
        Return True if this action data includes the attribute.
        This doesn't mean it has a value for the attribute, only
        that it can potentially.
        """
        return attrName in self.getAttrNames()

    def getAttrConfig(self, attrName):
        """
        Return config data for an attribute

        Args:
            attrName (str): The name of a BuildAction attribute
        """
        if not self.hasConfig():
            return

        for attr in self.config['attrs']:
            if attr['name'] == attrName:
                return attr

    def getAttrDefaultValue(self, attr):
        """
        Return the default value for an attribute

        Args:
            attr (dict): A BuildAction attribute config object
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

    def hasAttrValue(self, attrName):
        """
        Return True if this action data contains a non-default value
        for the attribute.

        Args:
            attrName (str): The name of a BuildAction attribute
        """
        return attrName in self._attrValues

    def getAttrValue(self, attrName, default=None):
        """
        Return the value for an attribute, or default if its
        value is not overridden in this action data.
        Use `getAttrValueOrDefault` to default to the config-default
        value for the attribute.

        Args:
            attrName (str): The name of a BuildAction attribute
        """
        return self._attrValues.get(attrName, default)

    def getAttrValueOrDefault(self, attrName):
        if attrName in self._attrValues:
            return self._attrValues[attrName]
        else:
            config = self.getAttrConfig(attrName)
            if config:
                return self.getAttrDefaultValue(config)
            else:
                LOG.warning("BuildActionData attribute "
                            "not found: {0}".format(attrName))

    def setAttrValue(self, attrName, value):
        if value is None:
            self.delAttrValue(attrName)
        else:
            self._attrValues[attrName] = value

    def delAttrValue(self, attrName):
        if attrName in self._attrValues:
            del self._attrValues[attrName]

    def serialize(self):
        """
        Return this BuildActionData as a serialized dict object
        """
        data = UnsortableOrderedDict()
        data['id'] = self._actionId
        if self.hasConfig():
            for attr in self.getAttrs():
                if self.hasAttrValue(attr['name']):
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
        if self.hasConfig():
            for attr in self.getAttrs():
                if attr['name'] in data:
                    self._attrValues[attr['name']] = data[attr['name']]

        elif len(data) > 1:
            # if config didn't load, don't throw away the attribute values
            LOG.warning(
                "Failed to find BuildAction config: {0}, "
                "preserving serialized attr values".format(self._actionId))
            for k, v in data.items():
                self._attrValues[k] = v


class BuildActionDataVariant(BuildActionData):
    """
    Contains a partial set of attribute values.
    """

    # TODO: prevent setting an attribute thats not in the variant

    def __init__(self, actionId=None):
        super(BuildActionDataVariant, self).__init__(actionId=actionId)
        # names of all attributes that are in this variant
        self._variantAttrs = []

    def getVariantAttrs(self):
        """
        Return the list of all variant attribute names
        """
        return self._variantAttrs

    def getAttrs(self):
        """
        Return all attrs for this BuildAction class

        Returns:
            A list of dict representing all attr configs
        """
        return [a for a in self.config['attrs'] if a['name'] in self.getVariantAttrs()]

    def getAttrNames(self):
        """
        Return a list of attribute names for this BuildAction class
        """
        if not self.hasConfig():
            return

        for attr in self.config['attrs']:
            if attr['name'] in self.getVariantAttrs():
                yield attr['name']

    def isVariantAttr(self, attrName):
        """
        Return True if the attribute is contained in this variant.
        This doesn't mean a non-default value is set for the attribute.

        Args:
            attrName (str): The name of a BuildAction attribute
        """
        return attrName in self.getVariantAttrs()

    def setIsVariantAttr(self, attrName, isVariant):
        """
        Set whether an attr is variant or not.

        Args:
            attrName (str): The name of a BuildAction attribute
            isVariant (bool): Whether the attribute should be variant or not
        """
        if isVariant:
            self.addVariantAttr(attrName)
        else:
            self.removeVariantAttr(attrName)

    def addVariantAttr(self, attrName):
        """
        Add an attribute to this variant.

        Args:
            attrName (str): The name of a BuildAction attribute
        """
        if attrName in self._variantAttrs:
            return

        if not self.hasAttrConfig(attrName):
            return

        self._variantAttrs.append(attrName)
        self._variantAttrs.sort()

    def removeVariantAttr(self, attrName):
        """
        Remove an attribute from the list of variant attributes,
        copying the value from the first variant into the default set
        of attr values if applicable.

        Args:
            attrName (str): The name of an action attribute
        """
        if attrName not in self._variantAttrs:
            return

        self._variantAttrs.remove(attrName)

        if self.hasAttrValue(attrName):
            self.delAttrValue(attrName)

    def clearVariantAttrs(self):
        """
        Remove all variant attributes, copying the values
        from the first variant into the default set of attr values
        if applicable.
        """
        attrNames = self._variantAttrs[:]
        for attrName in attrNames:
            self.removeVariantAttr(attrName)

    def serialize(self):
        data = super(BuildActionDataVariant, self).serialize()
        data['variantAttrs'] = self._variantAttrs
        return data

    def deserialize(self, data):
        # must deserialize attrs first before attempting
        # to set values in super deserialize
        self._variantAttrs = data.get('variantAttrs', [])

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

    The proxy provides a method `actionIterator` which performs the
    actual construction of BuildActions for use at build time.
    """

    def __init__(self, actionId=None):
        super(BuildActionProxy, self).__init__(actionId=actionId)
        # names of all attributes that are unique per variant
        self._variantAttrs = []
        # all BuildActionDataVariant instances in this proxy
        self._variants = []

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
        Return the full path to icon for this build action
        """
        filename = self.config.get('icon')
        configFile = self.config.get('configFile')
        if configFile:
            actiondir = os.path.dirname(configFile)
            if filename:
                return os.path.join(actiondir, filename)

    def isVariantAction(self):
        """
        Returns true of this action proxy has any variant attributes.
        """
        return bool(self._variantAttrs)

    def isVariantAttr(self, attrName):
        """
        Return True if the attribute is variant, meaning it is unique
        per each variant instance, and does not exist in the main
        action data.

        Args:
            attrName (str): The name of a BuildAction attribute
        """
        return attrName in self._variantAttrs

    def setIsVariantAttr(self, attrName, isVariant):
        """
        Set whether an attr is variant or not.

        Args:
            attrName (str): The name of a BuildAction attribute
            isVariant (bool): Whether the attribute should be variant or not
        """
        if isVariant:
            self.addVariantAttr(attrName)
        else:
            self.removeVariantAttr(attrName)

    def addVariantAttr(self, attrName):
        """
        Add an attribute to the list of variant attributes, removing
        any invariant values for the attribute, and creating
        variant values instead if applicable.

        Args:
            attrName (str): The name of an action attribute
        """
        if attrName in self._variantAttrs:
            return

        # add attr to variant attrs list
        self._variantAttrs.append(attrName)
        for variant in self._variants:
            variant.addVariantAttr(attrName)

        # if no variants exist, add one
        if self.numVariants() == 0:
            self.addVariant()

        # set the attribute value on all variants using
        # current invariant value if one exists
        if self.hasAttrValue(attrName):
            value = self.getAttrValue(attrName)
            self.delAttrValue(attrName)

            for variant in self._variants:
                if not variant.hasAttrValue(attrName):
                    variant.setAttrValue(attrName, value)

    def removeVariantAttr(self, attrName):
        """
        Remove an attribute from the list of variant attributes,
        copying the value from the first variant into the default set
        of attr values if applicable.

        Args:
            attrName (str): The name of an action attribute
        """
        if attrName not in self._variantAttrs:
            return

        # remove from attributes list
        self._variantAttrs.remove(attrName)

        # transfer first variant value to the invariant values
        if len(self._variants):
            firstVariant = self._variants[0]
            if firstVariant.hasAttrValue(attrName):
                value = firstVariant.getAttrValue(attrName)
                self.setAttrValue(attrName, value)

        # remove attr from variant instances
        for variant in self._variants:
            variant.removeVariantAttr(attrName)

    def getVariantAttrs(self):
        """
        Return the list of all variant attribute names
        """
        return self._variantAttrs

    def clearVariantAttrs(self):
        """
        Remove all variant attributes, copying the values
        from the first variant into the default set of attr values
        if applicable.
        """
        attrNames = self._variantAttrs[:]
        for attrName in attrNames:
            self.removeVariantAttr(attrName)

    def _createVariant(self):
        """
        Return a new BuildActionDataVariant instance
        for use with this action proxy.
        """
        variant = BuildActionDataVariant(actionId=self._actionId)
        for attrName in self._variantAttrs:
            variant.addVariantAttr(attrName)
        return variant

    def getVariant(self, index):
        """
        Return the BuildActionDataVariant instance at an index
        """
        return self._variants[index]

    def getOrCreateVariant(self, index):
        if index >= 0:
            while self.numVariants() <= index:
                self.addVariant()
        return self.getVariant(index)

    def numVariants(self):
        """
        Return how many variants exist on this action proxy
        """
        return len(self._variants)

    def addVariant(self):
        """
        Add a variant of attribute values. Does nothing if there
        are no variant attributes.
        """
        self._variants.append(self._createVariant())

    def insertVariant(self, index):
        """
        Insert a variant of attribute values. Does nothing if there
        are no variant attributes.

        Args:
            index (int): The index at which to insert the new variant
        """
        self._variants.insert(index, self._createVariant())

    def removeVariantAt(self, index):
        """
        Remove a variant of attribute values.

        Args:
            index (int): The index at which to remove the variant
        """
        count = len(self._variants)
        if index >= -count and index < count:
            del self._variants[index]

    def clearVariants(self):
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
                self.serializeVariant(v) for v in self._variants]
        return data

    def deserialize(self, data):
        super(BuildActionProxy, self).deserialize(data)
        self._variantAttrs = data.get('variantAttrs', [])
        self._variants = [
            self.deserializeVariant(v) for v in data.get('variants', [])]

    def serializeVariant(self, variant):
        data = variant.serialize()
        # prune unnecessary data from the variant for optimization
        del data['id']
        del data['variantAttrs']
        return data

    def deserializeVariant(self, data):
        variant = BuildActionDataVariant()
        # add necessary additional data for deserializing the variant
        data['id'] = self._actionId
        data['variantAttrs'] = self._variantAttrs
        variant.deserialize(data)
        return variant

    def actionIterator(self):
        """
        Generator that yields all the BuildActions represented
        by this proxy. If variants are in use, constructs a BuildAction
        for each set of variant attribute values.
        """
        if self.isActionIdValid():
            if self.isVariantAction():
                # ensure there are no invariant values for variant attrs
                for attrName in self._variantAttrs:
                    if self.hasAttrValue(attrName):
                        LOG.warning("Found invariant value for a variant attr: "
                                    "{0}.{1}".format(self.getActionId(), attrName))

                # create and yield new build actions for each variant
                mainData = self.serialize()
                for variant in self._variants:
                    # TODO: update serialization to ensure variants only return
                    #       data for the attributes they're supposed to modify
                    data = variant.serialize()
                    data.update(_copyData(mainData))
                    newAction = BuildAction.fromData(data)
                    yield newAction
            else:
                # no variants, just create one action
                yield BuildAction.fromData(_copyData(self.serialize()))


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

    def __repr__(self):
        return "<{0}>".format(self.__class__.__name__)

    def __getattr__(self, name):
        attrConfig = self.getAttrConfig(name)
        if attrConfig:
            if name in self._attrValues:
                return self._attrValues[name]
            else:
                return self.getAttrDefaultValue(attrConfig)
        else:
            raise AttributeError(
                "'{0}' object has no attribute '{1}'".format(type(self).__name__, name))

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
