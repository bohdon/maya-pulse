import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Optional, Iterable, List, Type, Set, Tuple

# TODO: remove maya dependencies from this core module, add BlueprintBuilder subclass that uses maya progress bars
import pymel.core as pm

from ..vendor import pymetanode as meta
from .. import names
from .blueprint import Blueprint, BlueprintSettings
from .rigs import RIG_METACLASS, create_rig_node
from .actions import BuildStep, BuildAction

__all__ = [
    "BlueprintBuilder",
    "BlueprintGlobalValidateStep",
    "BlueprintValidator",
]

LOG = logging.getLogger(__name__)


class BlueprintBuildLogHandler(logging.Handler):
    """
    Handler that sends logs to the blueprint builder so that it can track warnings and errors.
    """

    def __init__(self, builder: "BlueprintBuilder"):
        super().__init__()
        self.builder = builder

    def emit(self, record: logging.LogRecord):
        if self.builder:
            self.builder.notify_log(record)


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

        if not blueprint.root_step.has_any_children():
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

        self.is_started = False
        self.is_finished = False
        self.is_running = False
        self.is_canceled = False
        # if true, mark the build as cancelled when interrupted, instead of just pausing
        self.cancel_on_interrupt = True
        self.start_time = 0.0
        self.end_time = 0.0
        self.elapsed_time = 0.0
        self.show_progress_ui = True
        self.progress_title = "Building Blueprint"
        # the current context that should be associated with any warnings or errors that occur.
        # includes the current 'step' and 'action' when fully populated.
        self._log_context = {}
        # warnings that occurred during build
        self.warnings = []
        # errors that occurred during build
        self.errors = []

        self.generator: Optional[Iterable[dict]] = None
        # the current phase of building, 'setup', 'actions', or 'finished'
        self.phase: Optional[str] = None
        # the current build step path
        self.current_build_step_path: Optional[str] = None
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

        # create a logger for this build and setup handlers
        self.logger = logging.getLogger("pulse.build")
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        # reset handlers in case any are leftover
        self.logger.handlers = []

        # add filter to intercept logs and track warnings and errors
        self.build_log_handler = BlueprintBuildLogHandler(self)
        self.logger.addHandler(self.build_log_handler)

        self.file_handler: Optional[logging.FileHandler] = None
        self.setup_file_logger(log_dir)

    def has_errors(self) -> bool:
        return bool(self.errors)

    def get_error_summary(self) -> str:
        """
        Return a string representing the number of warnings or errors.

        Returns:
            "no errors" if no warnings or errors occurred.
            "{count} warnings" if only warnings occurred.
            "{count} errors" if any errors occurred.
        """
        if self.errors:
            count = len(self.errors)
            return f"{count} error{'s' if count > 1 else ''}"
        elif self.warnings:
            count = len(self.warnings)
            return f"{count} warning{'s' if count > 1 else ''}"
        return "no errors"

    def setup_file_logger(self, log_dir: str):
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

        self.logger.addHandler(self.file_handler)

    def close_file_logger(self):
        self.file_handler.close()

    def remove_log_handlers(self):
        self.logger.handlers = []

    def notify_log(self, record: logging.LogRecord):
        """
        Called when logging from this builders logger.
        Track warnings and errors and parse extra information to be able to present it
        in the build results.
        """
        if not self.is_started or self.is_finished or self.is_canceled:
            return

        if record.levelno == logging.WARNING:
            self.warnings.append(record)
        elif record.levelno == logging.ERROR:
            self._update_log_with_context(record)
            self.errors.append(record)
            # add the log to the current step
            step = self._get_log_step()
            if step:
                step.add_validate_error(record)

    def _update_log_with_context(self, record: logging.LogRecord):
        """
        Update a warning or error log with the current context.
        """
        extra = {}

        step: BuildStep = self._log_context.get("step")
        if step:
            extra["step_path"] = step.get_full_path()

        action: BuildAction = self._log_context.get("action")
        if action:
            extra["action_data"] = action.serialize()

        record.__dict__.update(extra)

    def _get_log_step(self) -> Optional[BuildStep]:
        """
        Return the current Build Step that should be associated with any warnings or errors.
        """
        if "step" in self._log_context:
            return self._log_context["step"]
        return self.blueprint.root_step

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
            self.logger.warning("Builder has already been started.")
            return False
        if self.is_finished:
            self.logger.error("Cannot re-start a builder that has already finished, make a new builder instead.")
            return False
        if self.is_canceled:
            self.logger.warning("Builder was cancelled, create a new instance to build again.")
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
            self.logger.error("Builder is already running.")
            return

        if not self.is_started:
            self.logger.error("Builder has not been started yet.")
            return

        if self.is_finished:
            self.logger.error("Builder has already finished.")
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
            self.logger.info(start_msg)

    def get_start_build_log_message(self) -> str:
        return f"Started building rig: {self.rig_name} (debug={self.debug})"

    def get_finish_build_log_message(self) -> str:
        return f"Built Rig '{self.rig_name}' with {self.get_error_summary()} ({self.elapsed_time:.3f}s)"

    def get_finish_build_in_view_message(self) -> str:
        if self.has_errors():
            return f"Build Finished with {self.get_error_summary()}"
        else:
            return "Build Successful"

    def get_cancel_log_message(self) -> str:
        return f"Cancelled build of rig '{self.rig_name}' with {self.get_error_summary()} ({self.elapsed_time:.3f}s)"

    def get_cancel_build_in_view_message(self) -> str:
        if self.has_errors():
            return f"Build Cancelled with {self.get_error_summary()}"
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
        lvl = logging.WARNING if self.has_errors() else logging.INFO
        self.logger.log(lvl, finish_msg)

        self.close_file_logger()
        self.remove_log_handlers()

        # show results with in-view message
        in_view_msg = self.get_finish_build_in_view_message()
        in_view_kwargs = {}
        if self.has_errors():
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
        lvl = logging.WARNING if self.has_errors() else logging.INFO
        self.logger.log(lvl, cancel_msg)

        self.close_file_logger()
        self.remove_log_handlers()

        # show cancellation with in-view message
        in_view_msg = self.get_cancel_build_in_view_message()
        in_view_kwargs = {}
        if self.has_errors():
            in_view_kwargs = dict(
                backColor=0xAA8336,
                fadeStayTime=3000,
            )
        pm.inViewMessage(assistMessage=in_view_msg, position="topCenter", fade=True, **in_view_kwargs)

    def action_iterator(self) -> Iterable[Tuple[BuildStep, BuildAction, int]]:
        """
        Return a generator that yields all BuildActions in the Blueprint.

        Returns:
            A generator that yields a tuple of (BuildStep, BuildAction, <variant or sym index>)
            for every action in the Blueprint.
        """
        for step in self.blueprint.root_step.child_iterator():
            self._log_context = dict(step=step)
            # try-catch each step, so we can stumble over
            # problematic steps without crashing the whole build
            try:
                index = 0
                for action in step.action_iterator(self.blueprint.get_config()):
                    yield step, action, index
                    index += 1
            except Exception as exc:
                self.logger.error(str(exc), exc_info=True)

        self._log_context = {}

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

        self._on_actions_generated(all_actions)

        for index, (step, action, action_index) in enumerate(all_actions):
            self.current_build_step_path = step.get_full_path()

            # return progress for the action that is about to run
            yield dict(index=index, total=action_count, phase="actions", status=self.current_build_step_path)

            # run the action
            action.builder = self
            action.rig = self.rig
            self._log_context = dict(step=step, action=action, action_index=action_index)
            self.run_build_action(step, action, action_index, index, action_count)
            self._log_context = {}

        yield dict(index=action_count, total=action_count, phase="finished", status="Finished")

    def clear_validate_results(self):
        """
        Clear the results of any previous validation or build.
        """
        self.blueprint.root_step.clear_validate_results()
        for step in self.blueprint.root_step.child_iterator():
            step.clear_validate_results()

    def create_rig_structure(self):
        """
        Create the top level rig node that will contain the entire rig.
        """
        node_name_format = self.blueprint.get_setting(BlueprintSettings.RIG_NODE_NAME_FORMAT)
        rig_node_name = node_name_format.format(**self.blueprint.settings)
        self.rig = create_rig_node(rig_node_name)

        # add some additional meta data
        meta.update_metadata(
            self.rig,
            RIG_METACLASS,
            dict(
                # TODO: update blueprint version when loaded,
                #       when saved and built it should be using the current version
                version=self.blueprint.version,
                blueprintFile=self.scene_file_path,
            ),
        )
        self.logger.info("Created rig structure: %s", self.rig.nodeName())

    def _generate_all_actions(self) -> List[Tuple[BuildStep, BuildAction, int]]:
        """
        Expand all build actions to perform from all build steps and their variants.
        """
        start_time = time.time()

        result = list(self.action_iterator())

        end_time = time.time()
        duration = end_time - start_time
        self.logger.info("Generated %s actions (%.03fs)", len(result), duration)
        return result

    def _on_actions_generated(self, all_actions: List[Tuple[BuildStep, BuildAction, int]]):
        """
        Called after all actions have been generated from variants and symmetry etc.
        Intended for use by subclasses that may need to post process or validate the actions.
        """
        pass

    def run_build_action(self, step: BuildStep, action: BuildAction, action_index: int, index: int, action_count: int):
        start_time = time.time()

        try:
            action.run()
        except Exception as exc:
            action.logger.error(str(exc), exc_info=True)

        end_time = time.time()
        duration = end_time - start_time

        path = step.get_full_path()
        self.logger.info("[%s/%s] %s[%d] (%.03fs)", index + 1, action_count, path, action_index, duration)


class BlueprintGlobalValidateStep(object):
    """
    Base class for a global validation step.

    Build actions can define their own global validate steps if they want to be
    able to validate the entire Blueprint holistically, e.g. to determine if there
    is a conflict between multiple actions or other high-level issues.
    """

    def __init__(
        self, blueprint: Blueprint, all_actions: List[Tuple[BuildStep, BuildAction, int]], logger: logging.Logger
    ):
        # the blueprint being validated
        self.blueprint = blueprint
        # the list of (step, action, action_index) for all expanded actions in the blueprint
        self.all_actions = all_actions
        # the logger to use for reporting errors
        self.logger = logger

    def validate(self):
        """
        Validate the blueprint, using `self.logger` to log any errors that were encountered.
        """
        raise NotImplementedError


class BlueprintValidator(BlueprintBuilder):
    """
    Runs `validate` for all BuildActions in a Blueprint.
    """

    def __init__(self, blueprint: Blueprint, scene_file_path: Optional[str] = None, debug=None, log_dir=None):
        super(BlueprintValidator, self).__init__(blueprint, scene_file_path, debug, log_dir)
        self.builder_name = "Validator"
        self.progress_title = "Validating Blueprint"
        self.show_progress_ui = False

    def setup_file_logger(self, log_dir: str):
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
        return f"Validated rig '{self.rig_name}' with {self.get_error_summary()} ({self.elapsed_time:.3f}s)"

    def get_finish_build_in_view_message(self):
        return f"Validate Finished with {self.get_error_summary()}"

    def _on_actions_generated(self, all_actions: List[Tuple[BuildStep, BuildAction, int]]):
        self.run_global_validates(all_actions)

    def run_global_validates(self, all_actions: List[Tuple[BuildStep, BuildAction, int]]):
        # gather list of validates to run
        validate_classes: Set[Type[BlueprintGlobalValidateStep]] = set()
        # action ids that have been gathered from, used to skip gathering more than once per type
        checked_action_ids: Set[str] = set()
        for step, action, _ in all_actions:
            if action.id not in checked_action_ids:
                checked_action_ids.add(action.id)
                for cls in action.global_validates:
                    validate_classes.add(cls)

        self.logger.debug(f"Running {len(validate_classes)} global validations.")

        # run all validates
        for cls in validate_classes:
            validator = cls(self.blueprint, all_actions, self.logger)
            validator.validate()

    def run_build_action(self, step: BuildStep, action: BuildAction, action_index: int, index: int, action_count: int):
        # validate attributes
        for attr_name, attr in action.get_attrs().items():
            attr.validate()
            if not attr.is_value_valid():
                reason = attr.get_invalid_reason()
                if reason == "required":
                    action.logger.error(f"{names.to_title(attr_name)} is not set.")
                else:
                    action.logger.error(f"{names.to_title(attr_name)} is not valid: {reason}")

        # run custom action validation
        try:
            action.run_validate()
        except Exception as exc:
            action.logger.error(str(exc), exc_info=True)
