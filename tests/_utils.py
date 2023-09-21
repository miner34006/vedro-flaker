from argparse import ArgumentParser, Namespace
from pathlib import Path
from time import monotonic_ns
from unittest.mock import Mock

import pytest
from vedro import Scenario
from vedro.core import (
    Config,
    ConfigType,
    Dispatcher,
    Factory,
    MonotonicScenarioScheduler,
    ScenarioResult,
    ScenarioScheduler,
    VirtualScenario,
)
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    ConfigLoadedEvent,
    ScenarioFailedEvent,
    StartupEvent,
)

from vedro_flaky_steps import FlakySteps, FlakyStepsPlugin
from vedro_flaky_steps import FlakyStepsScenarioScheduler as Scheduler


@pytest.fixture()
def dispatcher() -> Dispatcher:
    return Dispatcher()


@pytest.fixture()
def vedro_flaky_steps(dispatcher: Dispatcher) -> FlakyStepsPlugin:
    plugin = FlakyStepsPlugin(FlakySteps)
    plugin.subscribe(dispatcher)
    return plugin


@pytest.fixture()
def scheduler() -> Scheduler:
    return Scheduler([])


@pytest.fixture()
def scheduler_() -> Scheduler:
    return Mock(spec=Scheduler)


def setup_results(mock_obj):
    mock_obj.extra_details = []
    mock_obj.expected_errors_met = 0
    mock_obj.expected_errors_skipped = 0
    mock_obj.scenario_failures = set()
    return mock_obj


def setup_plugin(plugin_mock, subject: str = 'scneario_subject'):
    plugin_mock.current_scenario.scenario.subject = subject
    return plugin_mock


def make_vscenario() -> VirtualScenario:
    class _Scenario(Scenario):
        __file__ = Path(f"scenario_{monotonic_ns()}.py").absolute()

    return VirtualScenario(_Scenario, steps=[])


def make_scenario_result(has_expected_failure: bool = False) -> ScenarioResult:
    scenario_result = ScenarioResult(make_vscenario())
    setattr(scenario_result, "__vedro_flaky_steps__has_expected_failure__", has_expected_failure)
    return scenario_result


def make_config() -> ConfigType:
    class TestConfig(Config):
        class Registry(Config.Registry):
            ScenarioScheduler = Factory[ScenarioScheduler](MonotonicScenarioScheduler)

    return TestConfig


async def fire_arg_parsed_event(dispatcher: Dispatcher, reruns: int) -> None:
    config_loaded_event = ConfigLoadedEvent(Path(), make_config())
    await dispatcher.fire(config_loaded_event)

    arg_parse_event = ArgParseEvent(ArgumentParser())
    await dispatcher.fire(arg_parse_event)

    arg_parsed_event = ArgParsedEvent(Namespace(reruns=reruns))
    await dispatcher.fire(arg_parsed_event)


async def fire_startup_event(dispatcher: Dispatcher, scheduler: Scheduler) -> None:
    startup_event = StartupEvent(scheduler)
    await dispatcher.fire(startup_event)


async def fire_failed_event(dispatcher: Dispatcher,
                            has_expected_failure: bool = False) -> ScenarioFailedEvent:
    scenario_result = make_scenario_result(has_expected_failure).mark_failed()
    scenario_failed_event = ScenarioFailedEvent(scenario_result)
    await dispatcher.fire(scenario_failed_event)
    return scenario_failed_event
