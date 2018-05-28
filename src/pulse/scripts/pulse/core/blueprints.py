
import os
import logging
import traceback
import tempfile
import time
from datetime import datetime
from pulse.vendor import yaml
import pymel.core as pm
import maya.cmds as cmds
import pymetanode as meta

from .buildItems import BuildItem, BuildGroup
from .buildItems import getActionClass
from .rigs import RIG_METACLASS, createRigNode
from .. import version

__all__ = [
    'BLUEPRINT_METACLASS',
    'BLUEPRINT_NODENAME',
    'BLUEPRINT_VERSION',
    'Blueprint',
    'BlueprintBuilder',
]

LOG = logging.getLogger(__name__)
LOG.level = logging.DEBUG

BLUEPRINT_METACLASS = 'pulse_blueprint'
BLUEPRINT_VERSION = version.__version__
BLUEPRINT_NODENAME = 'pulse_blueprint'


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
    def createDefaultBlueprint():
        pm.cmds.undoInfo(openChunk=True, chunkName='Create Pulse Blueprint')
        blueprint = Blueprint()
        blueprint.initializeDefaultActions()
        blueprint.saveToDefaultNode()
        pm.cmds.undoInfo(closeChunk=True)

    @staticmethod
    def getDefaultNode():
        if pm.cmds.objExists(BLUEPRINT_NODENAME):
            return pm.PyNode(BLUEPRINT_NODENAME)

    @staticmethod
    def deleteDefaultNode():
        if pm.cmds.objExists(BLUEPRINT_NODENAME):
            pm.cmds.delete(BLUEPRINT_NODENAME)

    @staticmethod
    def doesDefaultNodeExist():
        return pm.cmds.objExists(BLUEPRINT_NODENAME)

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
        # the root BuildItem of this blueprint (a group with no name)
        self.rootItem = BuildGroup(displayName='')
        # the config file to use when designing this Blueprint
        # can be absolute, or relative to any python sys path
        pulseDir = os.path.dirname(os.path.join(__file__))
        self.configFile = os.path.realpath(
            os.path.join(pulseDir, 'config/default_blueprint_config.yaml'))

    def serialize(self):
        data = {}
        data['rigName'] = self.rigName
        data['version'] = self.version
        data['buildItems'] = self.rootItem.serialize()
        return data

    def deserialize(self, data):
        self.rigName = data['rigName']
        self.version = data['version']
        self.rootItem = BuildItem.create(data['buildItems'])

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
        st = time.time()
        meta.setMetaData(node, BLUEPRINT_METACLASS, data, replace=True)
        et = time.time()
        LOG.debug('blueprint save time: {0}s'.format(et - st))


    def saveToDefaultNode(self):
        self.saveToNode(BLUEPRINT_NODENAME, create=True)

    def loadFromNode(self, node):
        """
        Load Blueprint data from a node.

        Args:
            node: A PyNode or node name
        """
        if not Blueprint.isBlueprintNode(node):
            raise ValueError(
                "Node does not contain Blueprint data: {0}".format(node))
        data = meta.getMetaData(node, BLUEPRINT_METACLASS)
        self.deserialize(data)

    def loadFromDefaultNode(self):
        if pm.cmds.objExists(BLUEPRINT_NODENAME):
            self.loadFromNode(BLUEPRINT_NODENAME)
            return True
        return False

    def actionIterator(self):
        """
        Return the action iterator of the Blueprints root BuildGroup
        """
        return self.rootItem.actionIterator()

    def initializeDefaultActions(self):
        """
        Create a set of core BuildActions that are common in most
        if not all Blueprints.

        WARNING: This clears all BuildActions and replaces them
        with the default set.
        """
        importAction = getActionClass('ImportReferences')()
        hierAction = getActionClass('BuildCoreHierarchy')()
        hierAction.allNodes = True
        mainGroup = BuildGroup(displayName='Main')
        saveAction = getActionClass('SaveBuiltRig')()
        optimizeAction = getActionClass('OptimizeScene')()
        self.rootItem.children = [
            importAction,
            hierAction,
            mainGroup,
            saveAction,
            optimizeAction,
        ]

    def getBuildGroup(self, groupPath=''):
        """
        Return a BuildGroup by path. If no path
        is given, return the root BuildGroup.

        Args:
            groupPath: A string path to a BuildGroup,
                e.g. 'Main/MyGroup/MySubGroup'
        """
        groupNames = []
        if groupPath and groupPath != '/':
            groupNames = groupPath.split('/')
        currentGroup = self.rootItem
        for name in groupNames:
            currentGroup = currentGroup.getChildGroupByName(name)
            if not currentGroup:
                return
        return currentGroup

    def loadBlueprintConfig(self):
        """
        Load and return the config for this Blueprint.
        """
        if not os.path.isfile(self.configFile):
            cmds.warning("Config file not found: {0}".format(self.configFile))
            return

        with open(self.configFile, 'rb') as fp:
            return yaml.load(fp)


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
            blueprintFile: An optional string path to the maya file that contains
                the blueprint for the built rig. This path is stored in the built
                rig for convenience.

        """
        if not isinstance(blueprint, Blueprint):
            raise ValueError("Expected Blueprint, got {0}".format(
                type(blueprint).__name__))

        self.blueprint = blueprint
        self.blueprintFile = blueprintFile
        self.debug = debug

        self.log = logging.getLogger('pulse.build')
        # the output directory for log files
        dateStr = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        if not logDir:
            logDir = tempfile.gettempdir()
        logFile = os.path.join(logDir, 'pulse_build_{0}_{1}.log'.format(
            self.blueprint.rigName, dateStr))
        self.fileHandler = logging.FileHandler(logFile)
        self.fileHandler.setLevel(logging.DEBUG)
        logFormatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        self.fileHandler.setFormatter(logFormatter)
        self.log.handlers = [self.fileHandler]

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
            self.log.error(
                "Cannot re-start a builder that has already finished, make a new builder instead")
            return
        if self.isCancelled:
            self.log.warning(
                "Builder was cancelled, create a new instance to build again")
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
            self.log.warning(
                "Cannot run/continue a finished or cancelled build")
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
        self.log.info("Started building rig: {0}".format(
            self.blueprint.rigName))
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

        errorCount = len(self.errors)
        # log results
        logMsg = "Built Rig '{0}', {1:.3f} seconds, {2} error(s)".format(
            self.blueprint.rigName, self.elapsedTime, errorCount)
        lvl = logging.WARNING if errorCount else logging.INFO
        self.log.log(lvl, logMsg, extra=dict(
            duration=self.elapsedTime,
            scenePath=self.blueprintFile,
        ))
        self.fileHandler.close()

        # show results with in view message
        if errorCount:
            pm.inViewMessage(amg='Build Finished with {0} error(s)'.format(errorCount),
                             pos='topCenter', backColor=0xaa8336,
                             fade=True, fadeStayTime=3000)
        else:
            pm.inViewMessage(amg='Build Finished', pos='topCenter', fade=True)

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
            self.log.error('{0}'.format(
                action.getDisplayName()), exc_info=True)
            traceback.print_exc()
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
            version=BLUEPRINT_VERSION,
            blueprintFile=self.blueprintFile,
        ))

        yield dict(current=currentStep, total=totalSteps)

        # recursively iterate through all build items
        allActions = list(self.blueprint.actionIterator())
        totalSteps = len(allActions)
        for currentStep, (action, path) in enumerate(allActions):
            _path = path + ' - ' if path else ''
            self.log.info('[{0}/{1}] {path}{name}'.format(currentStep + 1,
                                                          totalSteps, path=_path, name=action.getDisplayName()))
            # run the action
            action.rig = self.rig
            try:
                action.run()
            except Exception as error:
                self._onError(action, error)
            # return progress
            yield dict(current=currentStep, total=totalSteps)

        # delete the blueprint node
        Blueprint.deleteDefaultNode()

        yield dict(current=currentStep, total=totalSteps, finish=True)
