from functools import wraps
from typing import Any, Callable
from ell.configurator import config
from ell.lmp._track import _track
from ell.stores.models import LMPType
from ell.util.verbosity import model_usage_logger_pre

def function(*, exempt_from_tracking: bool = False, _exempt_from_logging: bool = False, type = LMPType.FUNCTION, **function_kwargs):
    def function_decorator(fn: Callable[..., Any]):
        
        @wraps(fn)
        def wrapper(*args, _invocation_origin: str = None, **kwargs):
            should_log = not exempt_from_tracking and config.verbose and not _exempt_from_logging
            if should_log:
                model_usage_logger_pre(fn, args, kwargs, "[]", [])

            result = fn(*args, **kwargs)

            return result, {}, {}

        wrapper.__ell_func__ = fn
        wrapper.__ell_type__ = type
        wrapper.__ell_exempt_from_tracking = exempt_from_tracking

        if exempt_from_tracking:
            # Wrap to return only the result (not the 3-tuple)
            # This ensures consistent return behavior regardless of exempt_from_tracking setting
            @wraps(wrapper)
            def exempt_wrapper(*args, **kwargs):
                # Remove internal kwargs that shouldn't be passed through
                kwargs.pop('_invocation_origin', None)
                result, _, _ = wrapper(*args, **kwargs)
                return result
            exempt_wrapper.__ell_func__ = fn
            exempt_wrapper.__ell_type__ = type
            exempt_wrapper.__ell_exempt_from_tracking = exempt_from_tracking
            return exempt_wrapper
        else:
            return _track(wrapper)

    return function_decorator

# XXX: Fix wrapping of the wrong functional decorator.