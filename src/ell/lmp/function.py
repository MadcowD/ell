from typing import Any, Callable
from ell.configurator import config
from ell.lmp._track import _track
from ell.types.studio import LMPType
from ell.util.verbosity import model_usage_logger_pre

def function(*, exempt_from_tracking: bool = False, _exempt_from_logging: bool = False, lmp_type = LMPType.FUNCTION, **function_kwargs):
    def function_decorator(fn: Callable[..., Any]):
        def wrapper(*args, _invocation_origin: str = None, **kwargs):
            should_log = not exempt_from_tracking and config.verbose and not _exempt_from_logging
            if should_log:
                model_usage_logger_pre(fn, args, kwargs, "[]", [])

            result = fn(*args, **kwargs)

            return result, {}, {}

        wrapper.__ell_func__ = fn
        wrapper.__ell_type__ = lmp_type
        wrapper.__ell_exempt_from_tracking = exempt_from_tracking
        if exempt_from_tracking:
            return wrapper
        else:
            return _track(wrapper)

    return function_decorator

