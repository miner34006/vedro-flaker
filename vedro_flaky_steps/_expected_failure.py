import asyncio
import re
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

from vedro._scenario import Scenario

from ._flaky_steps_plugin import FlakyResults, FlakyStepsPlugin

__all__ = ("expected_failure",)


T = TypeVar("T", bound=Type[Scenario])


def is_expected_error(expected_error: str, actual_error: str) -> bool:
    assert expected_error
    return bool(re.search(expected_error, actual_error))


def expected_failure(expected_error_regexp: str, *,
                     continue_on_error: Optional[bool] = False,
                     comment: Optional[str] = None) -> Callable[[T], T]:
    def decorator(func: Callable) -> Callable:

        @contextmanager
        def do_wrapper_logic() -> None:
            FlakyStepsPlugin.has_flaky_decorator = True

            try:
                yield
            except Exception as err:
                if not FlakyStepsPlugin.is_enabled:
                    raise
                if not is_expected_error(expected_error_regexp, str(err)):
                    raise

                msg = f'Met expected error "{expected_error_regexp}" '\
                      f'in "{FlakyStepsPlugin.current_step}" step'
                FlakyResults.extra_details.append(msg)
                if comment:
                    FlakyResults.extra_details.append(comment)

                FlakyResults.expected_errors_met += 1
                setattr(FlakyStepsPlugin.current_scenario,
                        "__vedro_flaky_steps__has_expected_failure__", True)
                FlakyResults.scenario_failures.add(
                    FlakyStepsPlugin.current_scenario.scenario.subject)

                if continue_on_error:
                    setattr(FlakyStepsPlugin.current_scenario,
                            "__vedro_flaky_steps__has_expected_failure__", False)
                    FlakyResults.expected_errors_skipped += 1
                    return

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:  # type: ignore
            with do_wrapper_logic():
                return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:  # type: ignore
            with do_wrapper_logic():
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
