
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

from .buildItems import BuildStep
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
    a full rig. It is essentially made up of configuration settings
    and an ordered hierarchy of BuildActions.
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
    def createNode(nodeName):
        """
        Create a new Blueprint and save it to a node by name.

        Args:
            nodeName (str): The name of the new blueprint node to create

        Returns:
            (Blueprint, PyNode) of the new Blueprint and node
        """
        pm.cmds.undoInfo(openChunk=True, chunkName='Create Pulse Blueprint')
        blueprint = Blueprint()
        blueprint.initializeDefaultActions()
        node = blueprint.saveToNode(nodeName, create=True)
        pm.cmds.undoInfo(closeChunk=True)
        return blueprint, node

    @staticmethod
    def isBlueprintNode(node):
        """
        Return whether the given node is a Blueprint node
        """
        return meta.hasMetaClass(node, BLUEPRINT_METACLASS)

    @staticmethod
    def getAllBlueprintNodes():
        """
        Return all nodes in the scene with Blueprint data
        """
        return meta.findMetaNodes(BLUEPRINT_METACLASS)

    def __init__(self):
        # the name of the rig this blueprint represents
        self.rigName = 'newRig'
        # the version of this blueprint
        self.version = BLUEPRINT_VERSION
        # the root step of this blueprint
        self.rootStep = BuildStep('Root')
        # the config file to use when designing this Blueprint
        # can be absolute, or relative to any python sys path
        pulseDir = os.path.dirname(os.path.join(__file__))
        self.configFile = os.path.realpath(
            os.path.join(pulseDir, 'config/default_blueprint_config.yaml'))

    def serialize(self):
        data = {}
        data['rigName'] = self.rigName
        data['version'] = self.version
        data['steps'] = self.rootStep.serialize()
        return data

    def deserialize(self, data):
        self.rigName = data['rigName']
        self.version = data['version']
        self.rootStep.deserialize(data['steps'])

    def saveToNode(self, node, create=False):
        """
        Save this Blueprint to a node, creating a new node if desired.

        Args:
            node (PyNode or str): A node or node name
            create (bool): If true, create the node if necessary

        Returns:
            The node on which the blueprint was saved
        """
        if create and not pm.cmds.objExists(node):
            node = pm.cmds.createNode('network', n=node)
        data = self.serialize()
        st = time.time()
        meta.setMetaData(node, BLUEPRINT_METACLASS, data, replace=True)
        et = time.time()
        LOG.debug('blueprint save time: {0}s'.format(et - st))
        return node

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

    def actionIterator(self):
        """
        Generator that yields all BuildActions in this Blueprint.

        Returns:
            A generator that yields a tuple of (BuildStep, BuildAction)
            for every action in the Blueprint.
        """
        for step in self.rootStep.childIterator():
            for action in step.actionGenerator():
                yield step, action

    def getStepByPath(self, path):
        """
        Return a BuildStep from the Blueprint by path

        Args:
            path (string): A path pointing to a BuildStep
                e.g. My/Build/Step
        """
        return self.rootStep.getChildByPath(path)

    def initializeDefaultActions(self):
        """
        Create a set of core BuildActions that are common in most
        if not all Blueprints.

        WARNING: This clears all BuildActions and replaces them
        with the default set.
        """
        importAction = BuildStep(actionName='ImportReferences')
        hierAction = BuildStep(actionName='BuildCoreHierarchy')
        hierAction.action.allNodes = True
        mainGroup = BuildStep('Main')
        saveAction = BuildStep(actionName='SaveBuiltRig')
        optimizeAction = BuildStep(actionName='OptimizeScene')
        self.rootStep.addChild(importAction)
        self.rootStep.addChild(hierAction)
        self.rootStep.addChild(mainGroup)
        self.rootStep.addChild(saveAction)
        self.rootStep.addChild(optimizeAction)

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
            self.onProgress(iterResult['index'], iterResult['total'])
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

    def onProgress(self, index, total):
        """
        Called after every step of the build.
        Override this in subclasses to monitor progress.

        Args:
            index: An int representing the index of the current action
            total: An int representing the total number of actions
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
        It runs all BuildSteps and BuildActions in order.
        """
        currentActionIndex = 0
        totalActionCount = 0

        yield dict(index=currentActionIndex, total=totalActionCount)

        # create a new rig
        self.rig = createRigNode(self.blueprint.rigName)
        # add some additional meta data
        meta.updateMetaData(self.rig, RIG_METACLASS, dict(
            version=BLUEPRINT_VERSION,
            blueprintFile=self.blueprintFile,
        ))

        yield dict(index=currentActionIndex, total=totalActionCount)

        # recursively iterate through all build actions
        allActions = list(self.blueprint.actionIterator())
        totalActionCount = len(allActions)
        for currentActionIndex, (step, action) in enumerate(allActions):
            path = step.getFullPath()
            self.log.info(
                '[{0}/{1}] {path}'.format(currentActionIndex + 1, totalActionCount, path=path))

            # run the action
            action.rig = self.rig
            try:
                action.run()
            except Exception as error:
                self._onError(action, error)

            # return progress
            yield dict(index=currentActionIndex, total=totalActionCount)

        # delete all blueprint nodes
        for node in Blueprint.getAllBlueprintNodes():
            pm.delete(node)

        yield dict(index=currentActionIndex, total=totalActionCount, finish=True)
