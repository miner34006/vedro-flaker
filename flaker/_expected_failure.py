import asyncio
import re
from functools import wraps
from typing import Callable, Optional, Type, TypeVar

from vedro._scenario import Scenario

from ._flaker_plugin import FlakerPlugin

__all__ = ("expected_failure",)


T = TypeVar("T", bound=Type[Scenario])


def is_expected_error(expected_error: str, actual_error: str) -> bool:
    return bool(re.search(expected_error, actual_error))


def expected_failure(expected_error_regexp: str,
                     continue_on_error: Optional[bool] = False,
                     info_message: Optional[str] = None) -> Callable[[T], T]:
    def decorator(func: Callable):  # type: ignore
        @wraps(func)
        async def wrapper(*args, **kwargs):  # type: ignore
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as err:
                if not is_expected_error(expected_error_regexp, str(err)):
                    raise

                msg = f'Met expected error "{expected_error_regexp}" '\
                      f'in "{FlakerPlugin.current_step}" step'
                FlakerPlugin.extra_details.append(msg)
                if info_message:
                    FlakerPlugin.extra_details.append(info_message)

                FlakerPlugin.expected_errors_met += 1
                setattr(FlakerPlugin.current_scenario,
                        "__flaker__has_expected_failure__", True)
                FlakerPlugin.scenario_failures.add(FlakerPlugin.current_scenario.scenario.subject)

                if continue_on_error:
                    setattr(FlakerPlugin.current_scenario,
                            "__flaker__has_expected_failure__", False)
                    FlakerPlugin.expected_errors_skipped += 1
                    return

                raise

        return wrapper
    return decorator
