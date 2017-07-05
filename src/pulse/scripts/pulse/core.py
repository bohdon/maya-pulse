
import pymel.core as pm

import os
import logging
import time
import tempfile
import yaml
from datetime import datetime

import pymetanode as meta

from . import version


__all__ = [
    'Blueprint',
    'BLUEPRINT_METACLASS',
    'BlueprintBuilder',
    'BuildAction',
    'BuildActionError',
    'BuildGroup',
    'BuildItem',
    'getActionClass',
    'getBuildItemClass',
    'getRegisteredActions',
    'registerActions',
    'RIG_METACLASS',
]


LOG = logging.getLogger(__name__)


BLUEPRINT_METACLASS = 'pulse_blueprint'
BLUEPRINT_VERSION = version.__version__
BLUEPRINT_NODENAME = 'pulse_blueprint'

RIG_METACLASS = 'pulse_rig'

BUILDITEM_TYPEMAP = {}


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
        elif typeName in BUILDITEM_TYPEMAP:
            if BUILDITEM_TYPEMAP[typeName].config.get('isBuiltin', False):
                LOG.error("A built-in BuildAction already exists with type name: {0}".format(typeName))
                continue
        BUILDITEM_TYPEMAP[typeName] = c


def createRigNode(name):
    """
    Create and return a new Rig node

    Args:
        name: A str name of the rig
    """
    if pm.cmds.objExists(name):
        raise ValueError("Cannot create rig, node already exists: {0}".format(name))
    node = pm.group(name=name, em=True)
    # set initial meta data for the rig
    meta.setMetaData(node, RIG_METACLASS, {'name':name})
    return node


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

    def actionIterator(self, parentPath=None):
        """
        Yields all BuildActions in this BuildGroup,
        recursively handling child BuildGroups as well.

        Args:
            parentPath: A string path representing the parent BuildGroup
        """
        thisPath = '/'.join([parentPath, self.getDisplayName()]) if parentPath else self.getDisplayName()
        for index, item in enumerate(self.children):
            if isinstance(item, BuildGroup):
                for item2, index2, path2 in item.actionIterator(thisPath):
                    yield item2, index2, path2
            elif isinstance(item, BuildAction):
                yield item, index, thisPath


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

    def __init__(self):
        super(BuildAction, self).__init__()
        if self.config is None:
            LOG.warning(self.__class__.__name__ + " was loaded without a config. " +
                "Use pulse action loading methods to ensure BuildActions are loaded properly")
        # rig is only available during build
        self.rig = None
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
            if attr['name'] in data:
                setattr(self, attr['name'], data[attr['name']])
            else:
                self.log.warning('No serialized data for attribute: {0}'.format(attr['name']))
                setattr(self, attr['name'], self.getDefaultValue(attr))

    def updateRigMetaData(self, data):
        """
        Add some meta data to the rig.
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
        """
        Create a Blueprint instance from serialized data
        """
        blueprint = Blueprint()
        blueprint.deserialize(data)
        return blueprint

    @staticmethod
    def fromNode(node):
        """
        Load a Blueprint from a node.

        Args:
            node: A PyNode or node name containing blueprint data
        """
        blueprint = Blueprint()
        blueprint.loadFromNode(node)
        return blueprint

    @staticmethod
    def fromDefaultNode(create=False):
        """
        Return a Blueprint using the default blueprint node.
        Creates the default node if it does not exist.
        """
        if not pm.cmds.objExists(BLUEPRINT_NODENAME):
            if create:
                blueprint = Blueprint()
                blueprint.saveToDefaultNode()
                return blueprint
        else:
            return Blueprint.fromNode(BLUEPRINT_NODENAME)

    @staticmethod
    def isBlueprintNode(node):
        """
        Return whether the given node is a Blueprint node
        """
        return meta.hasMetaClass(node, BLUEPRINT_METACLASS)

    def __init__(self):
        # the name of the rig this blueprint represents
        self.rigName = 'newRig'
        # the version of this blueprint
        self.version = BLUEPRINT_VERSION
        # the root BuildGroup of this blueprint
        self.rootBuildItem = BuildGroup(displayName='')

    def serialize(self):
        data = {}
        data['rigName'] = self.rigName
        data['version'] = self.version
        data['buildItems'] = self.rootBuildItem.serialize()
        return data

    def deserialize(self, data):
        self.rigName = data['rigName']
        self.version = data['version']
        self.rootBuildItem = BuildItem.create(data['buildItems'])
        # ignore whatever display name was serialized for root item
        self.rootBuildItem.displayName = ''

    def saveToNode(self, node, create=False):
        """
        Save this Blueprint to a node, creating a new node if desired.

        Args:
            node: A PyNode or node name
            create: A bool, whether to create the node if it doesn't exist
        """
        if create and not pm.cmds.objExists(node):
            node = pm.cmds.createNode('network', n=node)
        data = self.serialize()
        meta.setMetaData(node, BLUEPRINT_METACLASS, data)

    def saveToDefaultNode(self):
        self.saveToNode(BLUEPRINT_NODENAME, create=True)

    def loadFromNode(self, node):
        """
        Load Blueprint data from a node.
        
        Args:
            node: A PyNode or node name
        """
        if not Blueprint.isBlueprintNode(node):
            raise ValueError("Node does not contain Blueprint data: {0}".format(node))
        data = meta.getMetaData(node, BLUEPRINT_METACLASS)
        self.deserialize(data)

    def loadFromDefaultNode(self):
        self.loadFromNode(BLUEPRINT_NODENAME)

    def initializeDefaultActions(self):
        """
        Create a set of core BuildActions that are common in most
        if not all Blueprints.

        WARNING: This clears all BuildActions and replaces them
        with the default set.
        """
        importAction = getActionClass('ImportReferences')()
        hierAction = getActionClass('BuildCoreHierarchy')()
        mainGroup = BuildGroup(displayName='Main')
        saveAction = getActionClass('SaveBuiltRig')()
        optimizeAction = getActionClass('OptimizeScene')()
        self.rootBuildItem.children = [
            importAction,
            hierAction,
            mainGroup,
            saveAction,
            optimizeAction,
        ]





class BlueprintBuilder(object):
    """
    The Blueprint Builder is responsible for turning a Blueprint
    into a fully realized rig. The only prerequisite is
    the Blueprint itself.
    """

    def __init__(self, blueprint, blueprintFile=None, debug=False, logDir=None):
        """
        Initialize a BlueprintBuilder

        Args:
            blueprint: A Blueprint to be built
            blueprintFile: A string path to the maya file containing the blueprint
                to be stored on the built rig for convenience

        """
        if not isinstance(blueprint, Blueprint):
            raise ValueError("Expected Blueprint, got {0}".format(type(blueprint).__name__))

        self.blueprint = blueprint
        self.blueprintFile = blueprintFile
        self.debug = debug

        self.log = logging.getLogger('pulse.build')
        # the output directory for log files
        dateStr = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        if not logDir:
            logDir = tempfile.gettempdir()
        logFile = os.path.join(logDir, 'pulse_build_{0}_{1}.log'.format(self.blueprint.rigName, dateStr))
        logHandler = logging.FileHandler(logFile)
        logHandler.setLevel(logging.DEBUG)
        logFormatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        logHandler.setFormatter(logFormatter)
        self.log.handlers = [logHandler]

        self.errors = []
        self.generator = None
        self.isStarted = False
        self.isFinished = False
        self.isRunning = False
        self.isCancelled = False
        self.startTime = None
        self.endTime = None
        self.elapsedTime = 0

    def start(self, run=True):
        """
        Start the build for the current blueprint
        
        Args:
            run: A bool, whether to automatically run the build once it
                is started or wait for `run` to be called manually
        """
        if self.isStarted:
            self.log.warning("Builder has already been started")
            return
        if self.isFinished:
            self.log.error("Cannot re-start a builder that has already finished, make a new builder instead")
            return
        if self.isCancelled:
            self.log.warning("Builder was cancelled, create a new instance to build again")
            return

        self.isStarted = True
        self.onStart()

        # start the build generator
        self.generator = self.buildGenerator()

        if run:
            self.run()

        return True

    def run(self):
        """
        Continue the current build

        The builder must be started by calling `start` first
        before this can be called
        """
        if self.isRunning:
            self.log.warning("Builder is already running")
            return
        if not self.isStarted:
            self.log.warning("Builder has not been started yet")
            return
        if self.isFinished or self.isCancelled:
            self.log.warning("Cannot run/continue a finished or cancelled build")
            return
        self.isRunning = True

        while True:
            iterResult = self.generator.next()
            # handle the result of the build iteration
            if iterResult.get('finish'):
                self.finish()
            # report progress
            self.onProgress(iterResult['current'], iterResult['total'])
            # check for user cancel
            if self.checkCancel():
                self.cancel()
            # check if we should stop running
            if self.isFinished or self.isCancelled or self.checkPause():
                break

        self.isRunning = False

    def checkPause(self):
        """
        Check for pause. Return True if the build should pause
        """
        return False

    def checkCancel(self):
        """
        Check for cancellation. Return True if the build should be canceled
        """
        return False

    def cancel(self):
        """
        Cancel the current build
        """
        self.isCancelled = True
        self.onCancel()

    def finish(self):
        """
        Finish the build by calling the appropriate finish methods
        """
        self.isFinished = True
        self.onFinish()


    def onStart(self):
        """
        Called right before the build starts
        """
        # record time
        self.startTime = time.time()
        # log start of build
        self.log.info("Started building rig: {0}".format(self.blueprint.rigName))
        if self.debug:
            self.log.info("Debug is enabled")

    def onProgress(self, current, total):
        """
        Called after every step of the build.
        Override this in subclasses to monitor progress.
        
        Args:
            current: An int representing the current build step
            total: An int representing the total number of build steps
        """
        pass

    def onFinish(self):
        """
        Called when the build has completely finished.
        """
        # record time
        self.endTime = time.time()
        self.elapsedTime = self.endTime - self.startTime
        # log results
        info = '{0:.3f} seconds, {1} error(s)'.format(self.elapsedTime, len(self.errors))
        lvl = logging.WARNING if len(self.errors) else logging.INFO
        self.log.log(lvl, "Built Rig '{0}', {1}".format(self.blueprint.rigName, info), extra=dict(
            duration=self.elapsedTime,
            scenePath=self.blueprintFile,
        ))

    def onCancel(self):
        """
        Called if the build was cancelled
        """
        pass

    def _onError(self, action, error):
        self.errors.append(error)
        self.onError(action, error)

    def onError(self, action, error):
        """
        Called when an error occurs while running a BuildAction

        Args:
            action: The BuildAction for which the error occurred
            error: The exception that occurred
        """
        if self.debug:
            # when debugging, show stack trace
            self.log.error('{0}'.format(action.getDisplayName()), exc_info=True)
        else:
            self.log.error('{0} : {1}'.format(action.getDisplayName(), error))


    def buildGenerator(self):
        """
        This is the main iterator for performing all build operations.
        It recursively traverses all BuildItems and runs them.
        """
        currentStep = 0
        totalSteps = 0

        yield dict(current=currentStep, total=totalSteps)

        # create a new rig
        self.rig = createRigNode(self.blueprint.rigName)
        # add some additional meta data
        meta.updateMetaData(self.rig, RIG_METACLASS, dict(
            version = BLUEPRINT_VERSION,
            blueprintFile = self.blueprintFile,
        ))

        # recursively iterate through all build items
        allActions = list(self.blueprint.rootBuildItem.actionIterator())
        totalSteps = len(allActions)
        for currentStep, (action, grpIndex, grpPath) in enumerate(allActions):
            path = '{0}[{1}] - '.format(grpPath, grpIndex) if grpPath else ''
            self.log.info('[{0}/{1}] {path}{name}'.format(currentStep, totalSteps, path=path, name=action.getDisplayName()))
            # run the action
            action.rig = self.rig
            try:
                action.run()
            except Exception as error:
                self._onError(action, error)
            # return progress
            yield dict(current=currentStep, total=totalSteps)

        # delete the default blueprint node if it exists
        if pm.cmds.objExists(BLUEPRINT_NODENAME):
            pm.cmds.delete(BLUEPRINT_NODENAME)

        yield dict(current=currentStep, total=totalSteps, finish=True)
