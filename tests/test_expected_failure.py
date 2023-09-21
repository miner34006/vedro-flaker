from unittest.mock import MagicMock, Mock, patch

import pytest
from baby_steps import given, then, when

from vedro_flaky_steps import expected_failure

from ._utils import setup_plugin, setup_results


@pytest.mark.asyncio
@patch('vedro_flaky_steps._expected_failure.FlakyResults')
async def test_function_executed_without_error(flaker_results: MagicMock):
    with given:
        mock_step = Mock()
        setup_results(flaker_results)
    with when:
        await expected_failure('.*')(mock_step)()
    with then:
        assert len(flaker_results.extra_details) == 0
        assert flaker_results.expected_errors_met == 0
        assert flaker_results.expected_errors_skipped == 0
        assert len(flaker_results.scenario_failures) == 0
        mock_step.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("continue_on_error", [True, False])
@patch('vedro_flaky_steps._expected_failure.FlakyResults')
async def test_function_executed_with_not_expected_error(flaker_results: MagicMock, continue_on_error: bool):
    with given:
        error_text = 'error'
        mock_step = Mock(side_effect=Exception(error_text))
        setup_results(flaker_results)

    with when:
        with pytest.raises(Exception, match=error_text):
            await expected_failure('aaaa', continue_on_error=continue_on_error)(mock_step)()

    with then:
        assert len(flaker_results.extra_details) == 0
        assert flaker_results.expected_errors_met == 0
        assert flaker_results.expected_errors_skipped == 0
        assert len(flaker_results.scenario_failures) == 0
        mock_step.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("comment", ['message', None])
@patch('vedro_flaky_steps._expected_failure.FlakyResults')
@patch('vedro_flaky_steps._expected_failure.FlakyStepsPlugin')
async def test_function_executed_with_expected_error_and_not_continue(flaker_plugin: MagicMock, flaker_results: MagicMock, comment: str):
    with given:
        subject = 'expected_subject'
        error_text = 'error'
        mock_step = Mock(side_effect=Exception(error_text))

        setup_results(flaker_results)
        setup_plugin(flaker_plugin, subject)

    with when:
        with pytest.raises(Exception, match=error_text):
            await expected_failure(expected_error_regexp=error_text,
                                continue_on_error=False,
                                comment=comment)(mock_step)()

    with then:
        expected_messages = 2 if comment else 1
        assert len(flaker_results.extra_details) == expected_messages
        assert flaker_results.expected_errors_met == 1
        assert flaker_results.expected_errors_skipped == 0
        assert subject in flaker_results.scenario_failures
        assert flaker_plugin.current_scenario.__vedro_flaky_steps__has_expected_failure__
        mock_step.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("comment", ['message', None])
@patch('vedro_flaky_steps._expected_failure.FlakyResults')
@patch('vedro_flaky_steps._expected_failure.FlakyStepsPlugin')
async def test_function_executed_with_expected_error_and_continue(flaker_plugin: MagicMock, flaker_results: MagicMock, comment: str):
    with given:
        subject = 'expected_subject'
        error_text = 'error'
        mock_step = Mock(side_effect=Exception(error_text))

        setup_results(flaker_results)
        setup_plugin(flaker_plugin, subject)

    with when:
        await expected_failure(expected_error_regexp=error_text,
                                continue_on_error=True,
                                comment=comment)(mock_step)()

    with then:
        expected_messages = 2 if comment else 1
        assert len(flaker_results.extra_details) == expected_messages
        assert flaker_results.expected_errors_met == 1
        assert flaker_results.expected_errors_skipped == 1
        assert subject in flaker_results.scenario_failures
        assert not flaker_plugin.current_scenario.__vedro_flaky_steps__has_expected_failure__
        mock_step.assert_called_once()
