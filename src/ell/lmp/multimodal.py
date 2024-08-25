from ell.configurator import config
from ell.lmp._track import _track
from ell._lstr import _lstr
from ell.types import Message, ContentBlock
from ell.types.message import LMP, InvocableLM, LMPParams, MessageOrDict, _lstr_generic
from ell.types.lmp import LMPType
from ell.util._warnings import _warnings
from ell.util.api import  call
from ell.util.verbosity import compute_color, model_usage_logger_pre


import openai

from functools import wraps
from typing import Any, Dict, Optional, List, Callable, Union

def complex(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, tools: Optional[List[Callable]] = None, post_callback: Optional[Callable] = None, **lm_kwargs):
    """
    Defines a basic language model program (a parameterization of an existing foundation model using a particular prompt.)

    This is a decorator that can be applied to any LMP type.
    """
    default_client_from_decorator = client


    def parameterized_lm_decorator(
        prompt: LMP,
    ) -> Callable[..., Union[List[Message], Message]]:
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

            (result, api_params, metadata) = call(model=model, messages=messages, lm_kwargs={**config.default_lm_params, **lm_kwargs, **lm_params}, client=client or default_client_from_decorator, _invocation_origin=_invocation_origin, _exempt_from_tracking=exempt_from_tracking, _logging_color=color, _name=prompt.__name__, tools=tools)
        
            result = post_callback(result) if post_callback else result
            
            return result, api_params, metadata


  
        # TODO: # we'll deal with type safety here later
        model_call.__ell_lm_kwargs__ = lm_kwargs
        model_call.__ell_func__ = prompt
        model_call.__ell_type__ = LMPType.LM
        model_call.__ell_exempt_from_tracking = exempt_from_tracking
        # model_call.__ell_uses__ = prompt.__ell_uses__
        # model_call.__ell_hash__ = prompt.__ell_hash__

        if exempt_from_tracking:
            return model_call
        else:
            return _track(model_call, forced_dependencies=dict(tools=tools))
    return parameterized_lm_decorator

def _get_messages(prompt_ret: Union[str, list[MessageOrDict]], prompt: LMP) -> list[Message]:
    """
    Helper function to convert the output of an LMP into a list of Messages.
    """
    if isinstance(prompt_ret, str):
        return [
            Message(role="system", content=[ContentBlock(text=_lstr(prompt.__doc__) or config.default_system_prompt)]),
            Message(role="user", content=[ContentBlock(text=prompt_ret)]),
        ]
    else:
        assert isinstance(
            prompt_ret, list
        ), "Need to pass a list of MessagesOrDict to the language model"
        return prompt_ret
