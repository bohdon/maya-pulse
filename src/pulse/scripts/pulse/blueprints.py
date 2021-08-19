import logging
import os
import tempfile
import time
from datetime import datetime

import maya.cmds as cmds
import pymel.core as pm

import pymetanode as meta
from . import version
from .buildItems import BuildStep
from .rigs import RIG_METACLASS, createRigNode
from .serializer import PulseDumper, PulseLoader, UnsortableOrderedDict
from .vendor import yaml

LOG = logging.getLogger(__name__)
LOG.level = logging.DEBUG

BLUEPRINT_VERSION = version.__version__


def getDefaultConfigFile():
    """
    Return the path to the default blueprint config file
    """
    pulseDir = os.path.dirname(os.path.dirname(os.path.join(__file__)))
    return os.path.realpath(
        os.path.join(pulseDir, 'config/default_blueprint_config.yaml'))


def loadDefaultConfig():
    """
    Load and return the default blueprint config
    """
    return _loadConfig(getDefaultConfigFile())


def _loadConfig(configFile):
    """
    Load and return the contents of a yaml config file
    """
    if not os.path.isfile(configFile):
        cmds.warning("Config file not found: {0}".format(configFile))
        return

    with open(configFile, 'r') as fp:
        return yaml.load(fp)


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

    def __init__(self):
        # the name of the rig this blueprint represents
        self.rigName = ''
        # the version of this blueprint
        self.version = BLUEPRINT_VERSION
        # the root step of this blueprint
        self.rootStep = BuildStep('Root')
        # the config file to use when designing this Blueprint
        self.configFile = getDefaultConfigFile()
        # the config, automatically loaded when calling `getConfig`
        self.config = None

    def isEmpty(self):
        """
        Return True if this Blueprint is empty.
        """
        if self.rigName.strip():
            return False
        if self.rootStep.numChildren > 0:
            return False
        return True

    def serialize(self):
        data = UnsortableOrderedDict()
        data['version'] = self.version
        data['rigName'] = self.rigName
        data['steps'] = self.rootStep.serialize()
        return data

    def deserialize(self, data):
        """
        Returns:
            True if the data was deserialized successfully
        """
        self.version = data.get('version', None)
        self.rigName = data.get('rigName', None)
        self.rootStep.deserialize(data.get('steps', {'name': 'Root'}))
        return True

    def loadFromFile(self, filepath):
        """
        Returns:
            True if the load was successful
        """
        LOG.debug("Loading blueprint: %s", filepath)

        try:
            with open(filepath, 'r') as fp:
                data = yaml.load(fp, Loader=PulseLoader)
        except IOError:
            return False

        if not data:
            return False

        return self.deserialize(data)

    def saveToFile(self, filepath):
        """
        Returns:
            True if the save was successful
        """
        sceneName = pm.sceneName()
        if not sceneName:
            return False

        LOG.debug("Saving blueprint: %s", filepath)

        data = self.serialize()
        with open(filepath, 'w') as fp:
            yaml.dump(data, fp, default_flow_style=False, Dumper=PulseDumper)

        return True

    def dumpYaml(self):
        data = self.serialize()
        return yaml.dump(data, default_flow_style=False, Dumper=PulseDumper)

    def loadFromYaml(self, yamlstr):
        """
        Load this Blueprint from a yaml string
        """
        try:
            data = yaml.load(yamlstr)
        except Exception:
            return False

        if not data:
            return False

        return self.deserialize(data)

    def getStepByPath(self, path):
        """
        Return a BuildStep from the Blueprint by path

        Args:
            path (string): A path pointing to a BuildStep
                e.g. My/Build/Step
        """
        if not path:
            return self.rootStep
        else:
            step = self.rootStep.getChildByPath(path)
            if not step:
                LOG.warning("could not find BuildStep: %s", path)
            return step

    def initializeDefaultActions(self):
        """
        Create a set of core BuildActions that are common in most
        if not all Blueprints.

        WARNING: This clears all BuildActions and replaces them
        with the default set.
        """
        importAction = BuildStep(actionId='Pulse.ImportReferences')
        hierAction = BuildStep(actionId='Pulse.BuildCoreHierarchy')
        hierAction.actionProxy.setAttrValue('allNodes', True)
        mainGroup = BuildStep('Main')
        renameAction = BuildStep(actionId='Pulse.RenameScene')
        self.rootStep.addChildren([
            importAction,
            hierAction,
            mainGroup,
            renameAction
        ])

    def getConfig(self):
        """
        Return the config for this Blueprint.
        Load the config from disk if it hasn't been loaded yet.
        """
        if self.config is None and self.configFile:
            self.loadConfig()
        return self.config

    def loadConfig(self):
        """
        Load the config for this Blueprint from the set `configFile`.
        Reloads the config even if it is already loaded.
        """
        if self.configFile:
            self.config = _loadConfig(self.configFile)


class BlueprintBuilder(object):
    """
    The Blueprint Builder is responsible for turning a Blueprint
    into a fully realized rig. The only prerequisite is
    the Blueprint itself.
    """

    @classmethod
    def preBuildValidate(cls, blueprint):
        # type: (class, Blueprint) -> bool
        """
        Perform a quick pre-build validation on a Blueprint
        to ensure that building can at least be started.
        """
        if not blueprint:
            LOG.error('No Blueprint was provided')
            return False

        if not blueprint.rigName:
            LOG.error('Rig name is not set')
            return False

        if not blueprint.rootStep.hasAnyChildren():
            LOG.error('Blueprint has no actions. Create new actions to begin.')
            return False

        return True

    @classmethod
    def createBuilderWithCurrentScene(cls, blueprint, debug=False):
        """
        Create and return a new BlueprintBuilder instance
        using a blueprint and the current scene.
        """
        blueprintFile = str(pm.sceneName())
        builder = cls(
            blueprint,
            blueprintFile=blueprintFile,
            debug=debug)
        return builder

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

        if not blueprint.rigName:
            raise ValueError("Blueprint rigName is not set")

        # the name of this builder object, used in logs
        self.builderName = 'Builder'

        self.errors = []
        self.generator = None
        self.isStarted = False
        self.isFinished = False
        self.isRunning = False
        self.isCancelled = False
        self.startTime = None
        self.endTime = None
        self.elapsedTime = 0
        self.showProgressUI = False

        # the rig root node, available after the builder starts,
        # and createRigStructure has been called
        self.rig = None

        self.blueprint = blueprint
        self.blueprintFile = blueprintFile
        self.debug = debug

        # create a logger, and setup a file handler
        self.log = logging.getLogger('pulse.build')
        self.log.setLevel(logging.DEBUG if self.debug else logging.INFO)
        self.setupFileLogger(self.log, logDir)

    def setupFileLogger(self, logger, logDir):
        """
        Create a file handler for the logger of this builder.
        """
        if not logDir:
            logDir = tempfile.gettempdir()

        # the output directory for log files
        dateStr = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        rigName = self.blueprint.rigName if self.blueprint else 'test'
        logFileName = 'pulse_build_{0}_{1}.log'.format(rigName, dateStr)
        logFile = os.path.join(logDir, logFileName)

        self.fileHandler = logging.FileHandler(logFile)
        self.fileHandler.setLevel(logging.DEBUG)

        logFormatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        self.fileHandler.setFormatter(logFormatter)

        logger.handlers = [self.fileHandler]

    def closeFileLogger(self):
        self.fileHandler.close()

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
            iterResult = next(self.generator)
            # handle the result of the build iteration
            if iterResult.get('finish'):
                self.finish()
            # report progress
            self.onProgress(iterResult['index'], iterResult['total'], iterResult['status'])
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
        startMsg = self.getStartBuildLogMessage()
        if startMsg:
            self.log.info(startMsg)

    def getStartBuildLogMessage(self):
        return "Started building rig: {0} (debug={1})".format(
            self.blueprint.rigName, self.debug)

    def onProgress(self, index, total, status):
        """
        Called after every step of the build.
        Override this in subclasses to monitor progress.

        Args:
            index: An int representing the index of the current action
            total: An int representing the total number of actions
            status (str): A status string representing the current step in progress
        """
        if self.showProgressUI:
            if index == 0:
                pm.progressWindow(t='Building Blueprint', min=0)
            pm.progressWindow(e=True, progress=index, max=total, status=status)
            # pm.refresh()

    def onFinish(self):
        """
        Called when the build has completely finished.
        """
        if self.showProgressUI:
            pm.progressWindow(e=True, status=None)
            pm.progressWindow(endProgress=True)

        # clear selection
        pm.select(cl=True)

        # record time
        self.endTime = time.time()
        self.elapsedTime = self.endTime - self.startTime

        # log results
        finishMsg = self.getFinishBuildLogMessage()

        errorCount = len(self.errors)
        lvl = logging.WARNING if errorCount else logging.INFO
        self.log.log(lvl, finishMsg, extra=dict(
            duration=self.elapsedTime,
            scenePath=self.blueprintFile,
        ))

        self.closeFileLogger()

        # show results with in view message
        inViewMsg = self.getFinishBuildInViewMessage()
        if errorCount:
            pm.inViewMessage(amg=inViewMsg,
                             pos='topCenter', backColor=0xaa8336,
                             fade=True, fadeStayTime=3000)
        else:
            pm.inViewMessage(amg=inViewMsg,
                             pos='topCenter', fade=True)

    def getFinishBuildLogMessage(self):
        errorCount = len(self.errors)
        return "Built Rig '{0}', {1:.3f} seconds, {2} error(s)".format(
            self.blueprint.rigName, self.elapsedTime, errorCount)

    def getFinishBuildInViewMessage(self):
        errorCount = len(self.errors)
        if errorCount > 0:
            return 'Build Finished with {0} error(s)'.format(errorCount)
        else:
            return 'Build Successful'

    def onCancel(self):
        """
        Called if the build was cancelled
        """
        pass

    def onError(self, error):
        """
        Called when a generic error occurs while running

        Args:
            error (Exception): The exception that occurred
        """
        self.errors.append(error)
        self.log.error(error, exc_info=self.debug)

    def onStepError(self, step, action, error):
        """
        Called when an error occurs while running a BuildAction

        Args:
            step (BuildStep): The step on which the error occurred
            action (BuildAction): The action or proxy for which the error occurred
            error (Exception): The exception that occurred
        """
        self.errors.append(error)
        self.log.error('/%s (%s): %s', step.getFullPath(),
                       action.getActionId(), error, exc_info=self.debug)

    def actionIterator(self):
        """
        Return a generator that yields all BuildActions in the Blueprint.

        Returns:
            A generator that yields a tuple of (BuildStep, BuildAction)
            for every action in the Blueprint.
        """
        for step in self.blueprint.rootStep.childIterator():
            # try-catch each step, so we can stumble over
            # problematic steps without crashing the whole build
            try:
                for action in step.actionIterator():
                    yield step, action
            except Exception as error:
                self.onStepError(step, step.actionProxy, error=error)

    def buildGenerator(self):
        """
        This is the main iterator for performing all build operations.
        It runs all BuildSteps and BuildActions in order.
        """

        yield dict(index=0, total=2, status='Create Rig Structure')

        self.createRigStructure()

        yield dict(index=1, total=2, status='Retrieve Actions')

        # recursively iterate through all build actions
        allActions = list(self.actionIterator())
        actionCount = len(allActions)
        for index, (step, action) in enumerate(allActions):
            # TODO: include more data somehow so we can track variant action indexes

            # return progress for the action that is about to run
            yield dict(index=index, total=actionCount, status=step.getFullPath())

            # run the action
            action.builder = self
            action.rig = self.rig
            self.runBuildAction(step, action, index, actionCount)

        yield dict(index=actionCount, total=actionCount, status='Finished', finish=True)

    def createRigStructure(self):
        # create a new rig
        self.rig = createRigNode(self.blueprint.rigName)
        # add some additional meta data
        meta.updateMetaData(self.rig, RIG_METACLASS, dict(
            version=BLUEPRINT_VERSION,
            blueprintFile=self.blueprintFile,
        ))

    def runBuildAction(self, step, action, index, actionCount):
        startTime = time.time()

        try:
            action.run()
        except Exception as error:
            self.onStepError(step, action, error)

        endTime = time.time()
        duration = endTime - startTime

        path = step.getFullPath()
        self.log.info('[%s/%s] %s (%.03fs)', index + 1, actionCount, path, duration)


class BlueprintValidator(BlueprintBuilder):
    """
    Runs `validate` for all BuildActions in a Blueprint.
    """

    def __init__(self, *args, **kwargs):
        super(BlueprintValidator, self).__init__(*args, **kwargs)
        self.builderName = 'Validator'

    def setupFileLogger(self, logger, logDir):
        # no file logging for validation
        pass

    def closeFileLogger(self):
        pass

    def createRigStructure(self):
        # do nothing, only validating
        pass

    def getStartBuildLogMessage(self):
        return

    def getFinishBuildLogMessage(self):
        errorCount = len(self.errors)
        return "Validated Rig '{0}': {1} error(s)".format(
            self.blueprint.rigName, errorCount)

    def getFinishBuildInViewMessage(self):
        errorCount = len(self.errors)
        return 'Validate Finished with {0} error(s)'.format(errorCount)

    def runBuildAction(self, step, action, index, actionCount):
        try:
            action.runValidate()
        except Exception as error:
            self.onStepError(step, action, error)
