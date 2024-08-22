from ell.configurator import config
from ell.decorators.track import track
from ell.types import LMP, InvocableLM, LMPParams, LMPType, _lstr_generic
from ell.util._warnings import _warnings
from ell.util.api import _get_lm_kwargs, _get_messages, _call
from ell.util.verbosity import compute_color, model_usage_logger_pre


import openai

from functools import wraps
from typing import Optional, List, Callable

def lm(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, tools: Optional[List[Callable]] = None, **lm_kwargs):
    """
    Defines a basic language model program (a parameterization of an existing foundation model using a particular prompt.)

    This is a decorator that can be applied to any LMP type.
    """
    default_client_from_decorator = client


    def parameterized_lm_decorator(
        prompt: LMP,
    ) -> InvocableLM:
        color = compute_color(prompt)
        _warnings(model, prompt, default_client_from_decorator)

            
        @wraps(prompt)
        def model_call(
            *fn_args,
            _invocation_origin : str = None,
            client: Optional[openai.Client] = None,
            lm_params: Optional[LMPParams] = {},
            invocation_kwargs=False,
            **fn_kwargs,
        ) -> _lstr_generic:
            res = prompt(*fn_args, **fn_kwargs)

            assert exempt_from_tracking or _invocation_origin is not None, "Invocation origin is required when using a tracked LMP"
            messages = _get_messages(res, prompt)

            if config.verbose and not exempt_from_tracking: model_usage_logger_pre(prompt, fn_args, fn_kwargs, "notimplemented", messages, color)

            final_lm_kwargs = _get_lm_kwargs(lm_kwargs, lm_params)
            api_params = dict(model=model, messages=messages, lm_kwargs=final_lm_kwargs, client=client or default_client_from_decorator)

            tracked_str, metadata = _call(**api_params, _invocation_origin=_invocation_origin, exempt_from_tracking=exempt_from_tracking, _logging_color=color, name=prompt.__name__, tools=tools)
            

            return tracked_str, api_params, metadata

        # TODO: # we'll deal with type safety here later
        model_call.__ell_lm_kwargs__ = lm_kwargs
        model_call.__ell_func__ = prompt
        model_call.__ell_type__ = LMPType.LM
        model_call.__ell_exempt_from_tracking = exempt_from_tracking

        if exempt_from_tracking:
            return model_call
        else:
            return track(model_call, forced_dependencies=dict(tools=tools))


    return parameterized_lm_decorator