from ell.configurator import config
from ell.decorators.track import track
from ell.types import LMP, InvocableLM, LMPParams, _lstr_generic
from ell.util._warnings import _warnings
from ell.util.lm import _get_lm_kwargs, _get_messages, _run_lm
from ell.util.verbosity import compute_color, model_usage_logger_pre


import openai

from functools import wraps
from typing import Optional


def lm(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False,  **lm_kwargs):
    """
    Defines a basic language model program (a parameterization of an existing foundation model using a particular prompt.)

    This is a decorator that can be applied to any LMP type.
    """
    default_client_from_decorator = client


    def decorator(
        fn: LMP,
    ) -> InvocableLM:
        color = compute_color(fn)
        _under_fn = fn


        _warnings(model, fn, default_client_from_decorator)

            
        @wraps(fn)
        def wrapper(
            *fn_args,
            _invocation_origin : str = None,
            client: Optional[openai.Client] = None,
            lm_params: LMPParams = {},
            invocation_kwargs=False,
            **fn_kwargs,
        ) -> _lstr_generic:
            res = fn(*fn_args, **fn_kwargs)

            assert exempt_from_tracking or _invocation_origin is not None, "Invocation orgiin is required when using a tracked LMP"
            messages = _get_messages(res, fn)

            if config.verbose and not exempt_from_tracking: model_usage_logger_pre(fn, fn_args, fn_kwargs, "notimplemented", messages, color)
            final_lm_kwargs = _get_lm_kwargs(lm_kwargs, lm_params)
            _invocation_kwargs = dict(model=model, messages=messages, lm_kwargs=final_lm_kwargs, client=client or default_client_from_decorator)
            tracked_str, metadata = _run_lm(**_invocation_kwargs, _invocation_origin=_invocation_origin, exempt_from_tracking=exempt_from_tracking, _logging_color=color)

            return tracked_str, _invocation_kwargs, metadata

        # TODO: # we'll deal with type safety here later
        wrapper.__ell_lm_kwargs__ = lm_kwargs
        wrapper.__ell_func__ = _under_fn
        wrapper.__ell_lm = True
        wrapper.__ell_exempt_from_tracking = exempt_from_tracking
        if exempt_from_tracking:
            return wrapper
        else:
            return track(wrapper)


    return decorator