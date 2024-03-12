from typing import List

from vedro.core import AggregatedResult, MonotonicScenarioScheduler, ScenarioResult

__all__ = ("FlakyStepsScenarioScheduler",)


def create_scenario_result_from_exsiting(scenario_result: ScenarioResult) -> ScenarioResult:
    result = ScenarioResult(scenario_result.scenario)
    result.set_scope(scenario_result.scope)

    for step_result in scenario_result.step_results:
        result.add_step_result(step_result)

    for artifact in scenario_result.artifacts:
        result.attach(artifact)

    for extra in scenario_result.extra_details:
        result.add_extra_details(extra)

    result.set_started_at(scenario_result.started_at)
    result.set_ended_at(scenario_result.ended_at)
    return result


class FlakyStepsScenarioScheduler(MonotonicScenarioScheduler):
    def aggregate_results(self, scenario_results: List[ScenarioResult]) -> AggregatedResult:
        assert len(scenario_results) > 0

        new_scenario_results = []
        for scenario_result in scenario_results:
            has_expected_failure = getattr(scenario_result,
                                           "__vedro_flaky_steps__has_expected_failure__", False)
            if scenario_result.is_failed() and has_expected_failure:
                new_result = create_scenario_result_from_exsiting(scenario_result)
                new_result.mark_passed()
                new_scenario_results.append(new_result)
            else:
                new_scenario_results.append(scenario_result)

        passed, failed = [], []
        for scenario_result in new_scenario_results:
            if scenario_result.is_passed():
                passed.append(scenario_result)
            elif scenario_result.is_failed():
                failed.append(scenario_result)

        if len(passed) == 0 and len(failed) == 0:
            result = new_scenario_results[-1]
        else:
            result = passed[-1] if len(passed) > len(failed) else failed[-1]

        return AggregatedResult.from_existing(result, new_scenario_results)
