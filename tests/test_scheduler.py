from typing import Callable, List

import pytest
from baby_steps import given, then, when
from pytest import raises
from vedro.core import AggregatedResult, MonotonicScenarioScheduler, ScenarioResult

from vedro_flaky_steps import FlakyStepsScenarioScheduler as Scheduler

from .conftest import make_scenario_result


def test_inheritance(scheduler: Scheduler):
    with when:
        res = isinstance(scheduler, MonotonicScenarioScheduler)

    with then:
        assert res


def test_aggregate_nothing(scheduler: Scheduler):
    with when, raises(BaseException) as exc:
        scheduler.aggregate_results([])

    with then:
        assert exc.type is AssertionError


def test_aggreate_skipped_with_expected_failures(scheduler: Scheduler):
    with given:
        scenario_results = [make_scenario_result(True).mark_skipped(),
                            make_scenario_result(False).mark_skipped()]

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result.is_skipped()


@pytest.mark.parametrize(
    "get_scenario_results", [
        lambda: [make_scenario_result(True).mark_passed()],
        lambda: [make_scenario_result(False).mark_passed()],
    ]
)
def test_aggregate_passed_with_expected_failure(
    get_scenario_results: Callable[[], List[ScenarioResult]], *, scheduler: Scheduler
):
    with given:
        scenario_results = get_scenario_results()

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result.is_passed()


def test_aggregate_2_passed_1_failed_without_expected_failures(scheduler: Scheduler):
    with given:
        passed_first = make_scenario_result().mark_passed()
        failed_single = make_scenario_result().mark_failed()
        passed_last = make_scenario_result().mark_passed()

        scenario_results = [passed_first, failed_single, passed_last]
        expected = AggregatedResult.from_existing(passed_last, scenario_results)

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result == expected


def test_aggregate_2_failed_1_passed_without_expected_failures(scheduler: Scheduler):
    with given:
        failed_first = make_scenario_result().mark_failed()
        passed_single = make_scenario_result().mark_passed()
        failed_last = make_scenario_result().mark_failed()

        scenario_results = [failed_first, passed_single, failed_last]
        expected = AggregatedResult.from_existing(failed_last, scenario_results)

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result == expected


def test_aggregate_2_passed_1_failed_with_expected_failure(scheduler: Scheduler):
    with given:
        passed_first = make_scenario_result().mark_passed()
        failed_single = make_scenario_result(True).mark_failed()
        passed_last = make_scenario_result().mark_passed()

        scenario_results = [passed_first, failed_single, passed_last]
        expected = AggregatedResult.from_existing(passed_last, scenario_results)

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result == expected


def test_aggregate_2_failed_1_passed_with_1_expected_failure(scheduler: Scheduler):
    with given:
        failed_first = make_scenario_result(True).mark_failed()
        passed_single = make_scenario_result().mark_passed()
        failed_last = make_scenario_result(False).mark_failed()

        scenario_results = [failed_first, passed_single, failed_last]

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result.is_passed()


@pytest.mark.parametrize(
    "get_scenario_results", [
        lambda: [make_scenario_result(True).mark_failed(),
                 make_scenario_result(False).mark_failed(),
                 make_scenario_result(False).mark_failed()],
        lambda: [make_scenario_result(False).mark_failed(),
                 make_scenario_result(True).mark_failed(),
                 make_scenario_result(False).mark_failed()],
        lambda: [make_scenario_result(False).mark_failed(),
                 make_scenario_result(False).mark_failed(),
                 make_scenario_result(True).mark_failed()],
    ]
)
def test_aggregate_3_failed_with_1_expected_failure(
    get_scenario_results: Callable[[], List[ScenarioResult]], *, scheduler: Scheduler
):
    with given:
        scenario_results = get_scenario_results()

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result.is_failed()


@pytest.mark.parametrize(
    "get_scenario_results", [
        lambda: [make_scenario_result(False).mark_failed(),
                 make_scenario_result(True).mark_failed(),
                 make_scenario_result(True).mark_failed()],
        lambda: [make_scenario_result(True).mark_failed(),
                 make_scenario_result(False).mark_failed(),
                 make_scenario_result(True).mark_failed()],
        lambda: [make_scenario_result(True).mark_failed(),
                 make_scenario_result(True).mark_failed(),
                 make_scenario_result(False).mark_failed()],
    ]
)
def test_aggregate_3_failed_with_2_expected_failures(
    get_scenario_results: Callable[[], List[ScenarioResult]], *, scheduler: Scheduler
):
    with given:
        scenario_results = get_scenario_results()

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result.is_passed()


def test_aggregate_with_all_types(scheduler: Scheduler):
    with given:
        scenario_results = [
            make_scenario_result(True).mark_failed(),
            make_scenario_result(False).mark_failed(),
            make_scenario_result(True).mark_passed(),
            make_scenario_result(False).mark_passed()
        ]

    with when:
        aggregated_result = scheduler.aggregate_results(scenario_results)

    with then:
        assert aggregated_result.is_passed()
