from typing import List

from vedro.core import AggregatedResult, MonotonicScenarioScheduler, ScenarioResult

__all__ = ("FlakyStepsScenarioScheduler",)



def create_new_scenario_result_from_exsiting(scenario_result):
    pass


class FlakyStepsScenarioScheduler(MonotonicScenarioScheduler):
    def aggregate_results(self, scenario_results: List[ScenarioResult]) -> AggregatedResult:
        assert len(scenario_results) > 0

        new_scenario_results = []
        for scenario_result in scenario_results:
            has_expected_failure = getattr(scenario_result,
                                           "__vedro_flaky_steps__has_expected_failure__", False)
            if scenario_result.is_failed() and has_expected_failure:
                new_result = ScenarioResult(scenario_result.scenario)
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
