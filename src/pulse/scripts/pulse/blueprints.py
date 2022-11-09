import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Optional, Iterable, List

# TODO: remove maya dependencies from this core module, add BlueprintBuilder subclass that uses maya progress bars
import pymel.core as pm

from .vendor import pymetanode as meta
from .vendor import yaml
from . import version
from .build_items import BuildStep, BuildAction, BuildActionData
from .rigs import RIG_METACLASS, create_rig_node
from .serializer import PulseDumper, PulseLoader, UnsortableOrderedDict

LOG = logging.getLogger(__name__)

BLUEPRINT_VERSION = version.__version__


def get_default_config_file() -> str:
    """
    Return the path to the default blueprint config file
    """
    pulse_dir = os.path.dirname(version.__file__)
    return os.path.realpath(os.path.join(pulse_dir, "config/default_blueprint_config.yaml"))


def load_default_config() -> Optional[dict]:
    """
    Load and return the default blueprint config
    """
    return _load_config(get_default_config_file())


def _load_config(file_path) -> Optional[dict]:
    """
    Load and return the contents of a yaml config file
    """
    if not os.path.isfile(file_path):
        LOG.warning("Config file not found: %s", file_path)
        return

    with open(file_path, "r") as fp:
        return yaml.load(fp)


class BlueprintSettings(object):
    """
    Constants defining the keys for Blueprint settings.
    """

    RIG_NAME = "rigName"
    RIG_NODE_NAME_FORMAT = "rigNodeNameFormat"
    DEBUG_BUILD = "debugBuild"


class Blueprint(object):
    """
    A Blueprint contains all the information necessary to build
    a full rig. It is essentially made up of configuration settings
    and an ordered hierarchy of BuildActions.
    """

    @staticmethod
    def from_data(data) -> "Blueprint":
        """
        Create a Blueprint instance from serialized data
        """
        blueprint = Blueprint()
        blueprint.deserialize(data)
        return blueprint

    def __init__(self):
        # various settings used by the blueprint, such as the rig name
        self.settings = {}
        self.add_missing_settings()
        # the version of this blueprint
        self.version: str = BLUEPRINT_VERSION
        # the root step of this blueprint
        self.rootStep: BuildStep = BuildStep("Root")
        # the config file to use when designing this Blueprint
        self.config_file_path: str = get_default_config_file()
        # the config, automatically loaded when calling `get_config`
        self._config: Optional[dict] = None

    def add_missing_settings(self):
        """
        Add new or missing settings to the Blueprint, do not overwrite any existing settings.
        """
        if BlueprintSettings.RIG_NAME not in self.settings:
            self.set_setting(BlueprintSettings.RIG_NAME, "")
        if BlueprintSettings.RIG_NODE_NAME_FORMAT not in self.settings:
            self.set_setting(BlueprintSettings.RIG_NODE_NAME_FORMAT, "{rigName}_rig")
        if BlueprintSettings.DEBUG_BUILD not in self.settings:
            self.set_setting(BlueprintSettings.DEBUG_BUILD, False)

    def get_setting(self, key: str, default=None):
        """
        Return a Blueprint setting by key.
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value):
        """
        Set a Blueprint setting by key.
        """
        self.settings[key] = value

    def serialize(self) -> UnsortableOrderedDict:
        data = UnsortableOrderedDict()
        data["version"] = self.version
        data["settings"] = self.settings
        data["steps"] = self.rootStep.serialize()
        return data

    def deserialize(self, data: dict) -> bool:
        """
        Returns:
            True if the data was deserialized successfully
        """
        self.version = data.get("version", None)
        self.settings = data.get("settings", {})
        self.rootStep.deserialize(data.get("steps", {"name": "Root"}))
        # inject new or missing settings
        self.add_missing_settings()
        return True

    def load_from_file(self, file_path: str) -> bool:
        """
        Returns:
            True if the load was successful
        """
        LOG.debug("Loading blueprint: %s", file_path)

        try:
            with open(file_path, "r") as fp:
                data = yaml.load(fp, Loader=PulseLoader)
        except IOError:
            return False

        if not data:
            return False

        return self.deserialize(data)

    def save_to_file(self, file_path: str) -> bool:
        """
        Returns:
            True if the save was successful
        """
        LOG.debug("Saving blueprint: %s", file_path)

        data = self.serialize()
        with open(file_path, "w") as fp:
            yaml.dump(data, fp, default_flow_style=False, Dumper=PulseDumper)

        return True

    def dump_yaml(self) -> str:
        data = self.serialize()
        return yaml.dump(data, default_flow_style=False, Dumper=PulseDumper)

    def load_from_yaml(self, yaml_str: str) -> bool:
        """
        Load this Blueprint from a yaml string
        """
        try:
            data = yaml.load(yaml_str)
        except Exception:
            return False

        if not data:
            return False

        return self.deserialize(data)

    def get_step_by_path(self, path: str) -> BuildStep:
        """
        Return a BuildStep from the Blueprint by path

        Args:
            path: str
                A path pointing to a BuildStep, e.g. 'My/Build/Step'
        """
        if not path:
            return self.rootStep
        else:
            step = self.rootStep.get_child_by_path(path)
            if not step:
                LOG.warning("Could not find BuildStep: %s", path)
            return step

    def add_default_actions(self):
        """
        Add a set of core BuildActions to the blueprint.
        """
        rename_action = BuildStep(action_id="Pulse.RenameScene")
        import_action = BuildStep(action_id="Pulse.ImportReferences")
        hierarchy_action = BuildStep(action_id="Pulse.BuildCoreHierarchy")
        hierarchy_attr = hierarchy_action.action_proxy.get_attr("allNodes")
        if hierarchy_attr:
            hierarchy_attr.set_value(True)
        main_group = BuildStep("Main")
        self.rootStep.add_children(
            [
                rename_action,
                import_action,
                hierarchy_action,
                main_group,
            ]
        )

    def get_config(self) -> dict:
        """
        Return the config for this Blueprint.
        Load the config from disk if it hasn't been loaded yet.
        """
        if self._config is None and self.config_file_path:
            self.load_config()
        return self._config

    def load_config(self):
        """
        Load the config for this Blueprint from the current file path.
        Reloads the config even if it is already loaded.
        """
        if self.config_file_path:
            self._config = _load_config(self.config_file_path)


class BlueprintFile(object):
    """
    Contains a Blueprint and file path info for saving and loading, as well as
    tracking modification status.

    A Blueprint File is considered valid by default, even without a file path,
    just like a new 'untitled' maya scene file. A file path must be assigned before it
    can be saved.
    """

    # the file extension to use for blueprint files
    file_ext: str = "yml"

    def __init__(self, file_path: Optional[str] = None, is_read_only: bool = False):
        self.blueprint = Blueprint()
        self.file_path = file_path
        self.is_read_only = is_read_only
        self._is_modified = False

    def has_file_path(self) -> bool:
        return bool(self.file_path)

    def can_load(self) -> bool:
        return self.has_file_path()

    def can_save(self) -> bool:
        return self.has_file_path() and not self.is_read_only

    def is_modified(self) -> bool:
        return self._is_modified

    def modify(self):
        """
        Mark the blueprint file as modified.
        """
        self._is_modified = True

    def clear_modified(self):
        """
        Clear the modified status of the file.
        """
        self._is_modified = False

    def get_file_name(self) -> Optional[str]:
        """
        Return the base name of the file path.
        """
        if self.file_path:
            return os.path.basename(self.file_path)

    def save(self) -> bool:
        """
        Save the Blueprint to file.

        Returns:
            True if the file was saved successfully.
        """
        if not self.file_path:
            LOG.warning("Cant save Blueprint, file path is not set.")
            return False

        success = self.blueprint.save_to_file(self.file_path)

        if success:
            self.clear_modified()
        else:
            LOG.error("Failed to save Blueprint to file: %s", self.file_path)

        return success

    def save_as(self, file_path: str) -> bool:
        """
        Save the Blueprint with a new file path.
        """
        self.file_path = file_path
        return self.save()

    def load(self) -> bool:
        """
        Load the blueprint from file.
        """
        if not self.file_path:
            LOG.warning("Cant load Blueprint, file path is not set.")
            return False

        if not os.path.isfile(self.file_path):
            LOG.warning("Blueprint file does not exist: %s", self.file_path)
            return False

        success = self.blueprint.load_from_file(self.file_path)

        if success:
            self.clear_modified()
        else:
            LOG.error("Failed to load Blueprint from file: %s", self.file_path)

        return success

    def resolve_file_path(self, allow_existing=False):
        """
        Automatically resolve the current file path based on the open maya scene.
        Does nothing if file path is already set.

        Args:
            allow_existing: bool
                If true, allow resolving to a path that already exists on disk.
        """
        if not self.file_path:
            file_path = self.get_default_file_path()
            if file_path:
                if allow_existing or not os.path.isfile(file_path):
                    self.file_path = file_path

    def get_default_file_path(self) -> Optional[str]:
        """
        Return the file path to use for a new blueprint file.
        Uses the open maya scene by default.

        # TODO: move out of core into a maya specific subclass
        """
        scene_name = pm.sceneName()

        if scene_name:
            base_name = os.path.splitext(scene_name)[0]
            return f"{base_name}.{self.file_ext}"


class BlueprintBuilder(object):
    """
    The Blueprint Builder is responsible for turning a Blueprint
    into a fully realized rig. The only prerequisite is
    the Blueprint itself.
    """

    @classmethod
    def pre_build_validate(cls, blueprint: Blueprint) -> bool:
        """
        Perform a quick pre-build validation on a Blueprint
        to ensure that building can at least be started.
        """
        if not blueprint:
            LOG.error("No Blueprint was provided")
            return False

        if not blueprint.get_setting(BlueprintSettings.RIG_NAME):
            LOG.error("Rig name is not set")
            return False

        if not blueprint.rootStep.has_any_children():
            LOG.error("Blueprint has no actions. Create new actions to begin.")
            return False

        return True

    @classmethod
    def from_current_scene(cls, blueprint: Blueprint) -> "BlueprintBuilder":
        """
        Create and return a new BlueprintBuilder instance
        using a blueprint and the current scene.
        """
        # TODO: embed scene path in Blueprint settings when created and use it instead of guess-associating here
        scene_file_path = str(pm.sceneName())
        builder = cls(blueprint, scene_file_path=scene_file_path)
        return builder

    def __init__(self, blueprint: Blueprint, scene_file_path: Optional[str] = None, debug=None, log_dir=None):
        """
        Initialize a BlueprintBuilder

        Args:
            blueprint: Blueprint
                A Blueprint to be built.
            scene_file_path: Optional[str]
                An optional string path to the maya file that contains the blueprint for the built rig.
                This path is stored in the built rig for convenience.
            log_dir: Optional[str]
                The directory where logs should be written.
        """
        if not blueprint.get_setting(BlueprintSettings.RIG_NAME):
            raise ValueError("Blueprint 'rigName' setting is not set.")

        # the name of this builder object, used in logs
        self.builder_name = "Builder"

        self.errors = []
        self.generator: Optional[Iterable[dict]] = None
        self.is_started = False
        self.is_finished = False
        self.is_running = False
        self.is_canceled = False
        # if true, mark the build as cancelled when interrupted, instead of just pausing
        self.cancel_on_interrupt = True
        # the current phase of building, 'setup', 'actions', or 'finished'
        self.phase: Optional[str] = None
        # the current build step path
        self.current_build_step_path: Optional[str] = None
        self.start_time = 0.0
        self.end_time = 0.0
        self.elapsed_time = 0.0
        self.show_progress_ui = True
        self.progress_title = "Building Blueprint"
        # the results of the last iteration that was performed
        self._iter_result = {}

        # the rig root node, available after the builder starts,
        # and create_rig_structure has been called
        self.rig: Optional[pm.nt.Transform] = None

        self.blueprint = blueprint
        self.scene_file_path = scene_file_path

        if debug is None:
            debug = self.blueprint.get_setting(BlueprintSettings.DEBUG_BUILD)
        self.debug = debug

        self.rig_name: str = self.blueprint.get_setting(BlueprintSettings.RIG_NAME)

        # create a logger, and setup a file handler
        self.log = logging.getLogger("pulse.build")
        self.log.setLevel(logging.DEBUG if self.debug else logging.INFO)
        self.file_handler: Optional[logging.FileHandler] = None
        self.setup_file_logger(self.log, log_dir)

    def setup_file_logger(self, logger: logging.Logger, log_dir: str):
        """
        Create a file handler for the logger of this builder.
        """
        if not log_dir:
            log_dir = tempfile.gettempdir()

        # the output directory for log files
        date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        rig_name = self.blueprint.get_setting(BlueprintSettings.RIG_NAME, "test")
        log_file_name = f"pulse_build_{rig_name}_{date_str}.log"
        log_file = os.path.join(log_dir, log_file_name)

        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setLevel(logging.DEBUG)

        log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        self.file_handler.setFormatter(log_formatter)

        logger.handlers = [self.file_handler]

    def close_file_logger(self):
        self.file_handler.close()

    def start(self, run=True) -> bool:
        """
        Start the build for the current blueprint

        Args:
            run: A bool, whether to automatically run the build once it
                is started or wait for `run` to be called manually

        Returns:
            True if the build was started.
        """
        if self.is_started:
            self.log.warning("Builder has already been started.")
            return False
        if self.is_finished:
            self.log.error("Cannot re-start a builder that has already finished, make a new builder instead.")
            return False
        if self.is_canceled:
            self.log.warning("Builder was cancelled, create a new instance to build again.")
            return False

        self.is_started = True
        self.on_start()

        # start the build generator
        self.generator = self.build_generator()

        if run:
            self.run()

        return True

    def run(self):
        """
        Continue the current build

        The builder must be started by calling `start` first
        before this can be called
        """
        if self.is_running:
            self.log.error("Builder is already running.")
            return

        if not self.is_started:
            self.log.error("Builder has not been started yet.")
            return

        if self.is_finished:
            self.log.error("Builder has already finished.")
            return

        self.is_running = True

        if self.show_progress_ui:
            pm.progressWindow(title=self.progress_title, minValue=0, progress=0, isInterruptable=True)

        while True:
            self.next()

            if self.show_progress_ui:
                pm.progressWindow(
                    edit=True,
                    progress=self._iter_result["index"],
                    maxValue=self._iter_result["total"],
                    status=self._iter_result["status"],
                )

            if not self.is_running or self.should_interrupt():
                if self.cancel_on_interrupt:
                    self.cancel()
                break

        if self.show_progress_ui:
            pm.progressWindow(edit=True, status=None)
            pm.progressWindow(endProgress=True)

        self.is_running = False

    def next(self):
        """
        Perform the next step of the build.
        """
        self._iter_result = next(self.generator)

        self.phase = self._iter_result["phase"]
        if self.phase == "finished":
            self.finish()

    def should_interrupt(self):
        """
        Return True if the running build should be interrupted.
        Checks for cancellation using the progress window when `show_progress_ui` is enabled.
        """
        if self.show_progress_ui:
            return pm.progressWindow(query=True, isCancelled=True)
        return False

    def pause(self):
        """
        Pause the current build if it is running.
        """
        self.is_running = False

    def cancel(self):
        if self.is_started and not self.is_finished:
            self.is_running = False
            self.is_canceled = True
            self.on_cancel()

    def finish(self):
        """
        Finish the build by calling the appropriate finish methods
        """
        self.is_running = False
        self.is_finished = True
        self.on_finish()

    def on_start(self):
        """
        Called right before the build starts
        """
        # record time
        self.start_time = time.time()
        # log start of build
        start_msg = self.get_start_build_log_message()
        if start_msg:
            self.log.info(start_msg)

    def get_start_build_log_message(self) -> str:
        return f"Started building rig: {self.rig_name} (debug={self.debug})"

    def get_finish_build_log_message(self) -> str:
        error_count = len(self.errors)
        return f"Built Rig '{self.rig_name}' with {error_count} error(s) ({self.elapsed_time:.3f}s)"

    def get_finish_build_in_view_message(self) -> str:
        error_count = len(self.errors)
        if error_count > 0:
            return f"Build Finished with {error_count} error(s)"
        else:
            return "Build Successful"

    def get_cancel_log_message(self) -> str:
        error_count = len(self.errors)
        return f"Cancelled build of rig '{self.rig_name}' with {error_count} error(s) ({self.elapsed_time:.3f}s)"

    def get_cancel_build_in_view_message(self) -> str:
        error_count = len(self.errors)
        if error_count > 0:
            return f"Build Cancelled with {error_count} error(s)"
        else:
            return "Build Cancelled"

    def _on_build_end(self):
        pm.select(clear=True)

        # record time
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time

    def on_finish(self):
        """
        Called when the build has completely finished.
        """
        self._on_build_end()

        # log results
        finish_msg = self.get_finish_build_log_message()
        had_errors = bool(self.errors)
        lvl = logging.WARNING if had_errors else logging.INFO
        self.log.log(lvl, finish_msg)

        self.close_file_logger()

        # show results with in-view message
        in_view_msg = self.get_finish_build_in_view_message()
        in_view_kwargs = {}
        if had_errors:
            in_view_kwargs = dict(
                backColor=0xAA8336,
                fadeStayTime=3000,
            )
        pm.inViewMessage(assistMessage=in_view_msg, position="topCenter", fade=True, **in_view_kwargs)

    def on_cancel(self):
        """
        Called when the build is cancelled.
        """
        self._on_build_end()

        # log results
        cancel_msg = self.get_cancel_log_message()
        had_errors = bool(self.errors)
        lvl = logging.WARNING if had_errors else logging.INFO
        self.log.log(lvl, cancel_msg)

        self.close_file_logger()

        # show cancellation with in-view message
        in_view_msg = self.get_cancel_build_in_view_message()
        in_view_kwargs = {}
        if had_errors:
            in_view_kwargs = dict(
                backColor=0xAA8336,
                fadeStayTime=3000,
            )
        pm.inViewMessage(assistMessage=in_view_msg, position="topCenter", fade=True, **in_view_kwargs)

    def on_error(self, error: Exception):
        """
        Called when a generic error occurs while running

        Args:
            error: Exception:
                The exception that occurred.
        """
        self.errors.append(error)
        self.log.error(error, exc_info=self.debug)

    def on_step_error(self, step: BuildStep, action: BuildActionData, exc: Exception):
        """
        Called when an error occurs while running a BuildAction

        Args:
            step: BuildStep
                The step on which the error occurred.
            action: BuildActionData
                The action or proxy for which the error occurred.
            exc: Exception
                The exception that occurred.
        """
        step.add_validate_error(exc)

        self.errors.append(exc)
        self.log.error("/%s (%s): %s", step.get_full_path(), action.action_id, exc, exc_info=self.debug)

    def action_iterator(self) -> Iterable[tuple[BuildStep, BuildAction]]:
        """
        Return a generator that yields all BuildActions in the Blueprint.

        Returns:
            A generator that yields a tuple of (BuildStep, BuildAction)
            for every action in the Blueprint.
        """
        for step in self.blueprint.rootStep.child_iterator():
            # try-catch each step, so we can stumble over
            # problematic steps without crashing the whole build
            try:
                for action in step.action_iterator(self.blueprint.get_config()):
                    yield step, action
            except Exception as exc:
                self.on_step_error(step, step.action_proxy, exc=exc)

    def build_generator(self) -> Iterable[dict]:
        """
        This is the main iterator for performing all build operations.
        It runs all BuildSteps and BuildActions in order.
        """

        self.clear_validate_results()

        yield dict(index=0, total=100, phase="setup", status="Create Rig Structure")
        self.create_rig_structure()

        yield dict(index=1, total=100, phase="setup", status="Retrieve Actions")
        all_actions = self._generate_all_actions()
        action_count = len(all_actions)

        for index, (step, action) in enumerate(all_actions):
            # TODO: include more data somehow so we can track variant action indexes

            # return progress for the action that is about to run
            self.current_build_step_path = step.get_full_path()
            yield dict(index=index, total=action_count, phase="actions", status=self.current_build_step_path)

            # run the action
            action.builder = self
            action.rig = self.rig
            self.run_build_action(step, action, index, action_count)

        yield dict(index=action_count, total=action_count, phase="finished", status="Finished")

    def clear_validate_results(self):
        """
        Clear the results of any previous validation or build.
        """
        for step in self.blueprint.rootStep.child_iterator():
            step.clear_validate_results()

    def create_rig_structure(self):
        """
        Create the top level rig node that will contain the entire rig.
        """
        node_name_format = self.blueprint.get_setting(BlueprintSettings.RIG_NODE_NAME_FORMAT)
        rig_node_name = node_name_format.format(**self.blueprint.settings)
        self.rig = create_rig_node(rig_node_name)

        # add some additional meta data
        meta.updateMetaData(
            self.rig,
            RIG_METACLASS,
            dict(
                version=BLUEPRINT_VERSION,
                blueprintFile=self.scene_file_path,
            ),
        )
        self.log.info("Created rig structure: %s", self.rig.nodeName())

    def _generate_all_actions(self) -> List[BuildAction]:
        """
        Expand all build actions to perform from all build steps and their variants.
        """
        start_time = time.time()

        result = list(self.action_iterator())

        end_time = time.time()
        duration = end_time - start_time
        self.log.info("Generated %s actions (%.03fs)", len(result), duration)
        return result

    def run_build_action(self, step: BuildStep, action: BuildAction, index: int, action_count: int):
        start_time = time.time()

        try:
            action.run()
        except Exception as error:
            self.on_step_error(step, action, error)

        end_time = time.time()
        duration = end_time - start_time

        path = step.get_full_path()
        self.log.info("[%s/%s] %s (%.03fs)", index + 1, action_count, path, duration)


class BlueprintValidator(BlueprintBuilder):
    """
    Runs `validate` for all BuildActions in a Blueprint.
    """

    def __init__(self, *args, **kwargs):
        super(BlueprintValidator, self).__init__(*args, **kwargs)
        self.builder_name = "Validator"
        self.progress_title = "Validating Blueprint"
        self.show_progress_ui = False

    def setup_file_logger(self, logger: logging.Logger, log_dir: str):
        # no file logging for validation
        pass

    def close_file_logger(self):
        pass

    def create_rig_structure(self):
        # do nothing, only validating
        pass

    def get_start_build_log_message(self):
        return f"Started validating blueprint: {self.rig_name} (debug={self.debug})"

    def get_finish_build_log_message(self):
        error_count = len(self.errors)
        return f"Validated rig '{self.rig_name}' with {error_count} error(s) ({self.elapsed_time:.3f}s)"

    def get_finish_build_in_view_message(self):
        error_count = len(self.errors)
        return f"Validate Finished with {error_count} error(s)"

    def run_build_action(self, step: BuildStep, action: BuildAction, index: int, action_count: int):
        try:
            action.run_validate()
        except Exception as error:
            self.on_step_error(step, action, error)
