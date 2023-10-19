from typing import List, Set, Tuple, Type, Union

from vedro.core import ConfigType, Dispatcher, Plugin, PluginConfig, ScenarioScheduler
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    CleanupEvent,
    ConfigLoadedEvent,
    ScenarioFailedEvent,
    ScenarioPassedEvent,
    ScenarioRunEvent,
    StartupEvent,
    StepRunEvent,
    VirtualScenario,
)

from ._scheduler import FlakyStepsScenarioScheduler

__all__ = ("FlakySteps", "FlakyStepsPlugin",)


class FlakyResults:
    # Aggregation values for reporting
    scenario_failures: Set[str] = set()
    expected_errors_met: int = 0
    expected_errors_skipped: int = 0
    extra_details: List[str] = []


class FlakyStepsPlugin(Plugin):
    current_step: Union[str, None] = None
    current_scenario = None
    is_enabled = False
    has_flaky_decorator = False

    def __init__(self, config: Type["FlakySteps"]) -> None:
        super().__init__(config)
        self._global_config: Union[ConfigType, None] = None
        self._scheduler_factory = config.scheduler_factory
        self._scheduler: Union[ScenarioScheduler, None] = None
        self._rerun_scenario_id: Union[str, None] = None
        self._add_allure_tag = config.add_flaky_tag
        self._flaky_tag_name = config.flaky_tag_name
        self._reruns: int = 0
        self._reran: int = 0
        self._times: int = 0

    def subscribe(self, dispatcher: Dispatcher) -> None:
        dispatcher\
            .listen(ConfigLoadedEvent, self.on_config_loaded)\
            .listen(ArgParseEvent, self.on_arg_parse) \
            .listen(ArgParsedEvent, self.on_arg_parsed) \
            .listen(StartupEvent, self.on_startup) \
            .listen(ScenarioRunEvent, self.on_scenario_run)\
            .listen(StepRunEvent, self.on_step_run) \
            .listen(CleanupEvent, self.on_cleanup)\
            .listen(ScenarioPassedEvent, self.on_scenario_end) \
            .listen(ScenarioFailedEvent, self.on_scenario_end)

    def on_config_loaded(self, event: ConfigLoadedEvent) -> None:
        FlakyStepsPlugin.is_enabled = True
        self._global_config = event.config

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        group = event.arg_parser.add_argument_group("FlakySteps")
        group.add_argument("--reruns", type=int, default=0,
                           help="Number of times to rerun failed scenarios (default: 0)")
        group.add_argument("--add-flaky-tag",
                           action='store_true',
                           default=self._add_allure_tag,
                           help="Add allure flaky tag when expected_failure is used")
        group.add_argument("--flaky-tag-name",
                           type=str,
                           default=self._flaky_tag_name,
                           help="Allure tag to use for flaky scenarios")

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        self._reruns = event.args.reruns
        if self._reruns < 0:
            raise ValueError("--reruns must be >= 0")

        self._add_allure_tag = event.args.add_flaky_tag
        self._flaky_tag_name = event.args.flaky_tag_name

        assert self._global_config is not None  # for type checking
        self._global_config.Registry.ScenarioScheduler.register(self._scheduler_factory, self)

    def on_startup(self, event: StartupEvent) -> None:
        self._scheduler = event.scheduler

    def on_scenario_run(self, event: ScenarioRunEvent) -> None:
        FlakyStepsPlugin.has_flaky_decorator = False
        FlakyStepsPlugin.current_scenario = event.scenario_result
        setattr(FlakyStepsPlugin.current_scenario,
                "__vedro_flaky_steps__has_expected_failure__", False)
        FlakyResults.extra_details = []

    def on_step_run(self, event: StepRunEvent) -> None:
        FlakyStepsPlugin.current_step = event.step_result.step_name

    def on_scenario_end(self, event: Union[ScenarioPassedEvent, ScenarioFailedEvent]) -> None:
        if FlakyStepsPlugin.has_flaky_decorator and self._add_allure_tag:
            self._add_flaky_tag(event.scenario_result.scenario, self._flaky_tag_name)

        for extra in FlakyResults.extra_details:
            event.scenario_result.add_extra_details(extra)

        if self._reruns == 0:
            return

        if self._rerun_scenario_id == event.scenario_result.scenario.unique_id:
            return

        self._rerun_scenario_id = event.scenario_result.scenario.unique_id
        has_expected_failure = \
            getattr(event.scenario_result, "__vedro_flaky_steps__has_expected_failure__", False)
        if event.scenario_result.is_failed() and not has_expected_failure:
            self._reran += 1
            for _ in range(self._reruns):
                self._scheduler.schedule(event.scenario_result.scenario)
                self._times += 1

    def on_cleanup(self, event: CleanupEvent) -> None:
        if self._reruns != 0:
            ss = "" if self._reran == 1 else "s"
            ts = "" if self._times == 1 else "s"
            event.report.add_summary(f"rerun {self._reran} scenario{ss}, {self._times} time{ts}")

        if FlakyResults.expected_errors_met == 0:
            return

        msg = f"{FlakyResults.expected_errors_met} expected errors met in "\
              f"{len(FlakyResults.scenario_failures)} scenarios, "\
              f"{FlakyResults.expected_errors_skipped} errors skipped"
        event.report.add_summary(msg)

    def _get_scenario_tags(self, scenario: VirtualScenario) -> Tuple[str, ...]:
        return getattr(scenario._orig_scenario, "tags", ())

    def _add_flaky_tag(self, scenario: VirtualScenario, tag_name: str) -> None:
        scenario_tags = self._get_scenario_tags(scenario)
        if tag_name in scenario_tags:
            return

        scenario_tags = list(scenario_tags)
        scenario_tags.append(tag_name)
        setattr(scenario._orig_scenario, "tags", tuple(scenario_tags))


class FlakySteps(PluginConfig):
    plugin = FlakyStepsPlugin
    description = "Mark expected errors in test steps"

    # Scheduler that will be used to create aggregated result for flaky scenarios
    scheduler_factory: Type[ScenarioScheduler] = FlakyStepsScenarioScheduler

    # Add flaky tag when expected_failure is used
    add_flaky_tag = False

    flaky_tag_name = 'flaky'
