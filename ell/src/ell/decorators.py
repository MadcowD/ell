"""
The core declarative functionality of the ell language model programming library.
"""

# This isn't fully accurate because we should enable the user to apply images and other multimodal inputs but we can address this now.
from collections import defaultdict
from functools import wraps
import hashlib
import json
import secrets
import time
import ell.util.closure
import colorama
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union, cast
from ell.configurator import  config
from ell.lstr import lstr
from ell.types import LMP, InvocableLM, LMPParams, Message, MessageOrDict, _lstr_generic
from ell.util.verbosity import  model_usage_logger_post_end, model_usage_logger_post_intermediate, model_usage_logger_post_start, model_usage_logger_pre, compute_color
import numpy as np
import openai
import cattrs

from datetime import datetime


import logging
colorama.Style


logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."
DEFAULT_LM_PARAMS: Dict[str, Any] = dict()


def _get_messages(res: Union[str, list[MessageOrDict]], fn: LMP) -> list[Message]:
    """
    Helper function to convert the output of an LMP into a list of Messages.
    """
    if isinstance(res, str):
        return [
            Message(role="system", content=(fn.__doc__) or DEFAULT_SYSTEM_PROMPT),
            Message(role="user", content=res),
        ]
    else:
        assert isinstance(
            res, list
        ), "Need to pass a list of MessagesOrDict to the language model"
        return res


def _get_lm_kwargs(lm_kwargs: Dict[str, Any], lm_params: LMPParams) -> Dict[str, Any]:
    """
    Helper function to combine the default LM parameters with the provided LM parameters and the parameters passed to the LMP.
    """
    final_lm_kwargs = dict(**DEFAULT_LM_PARAMS)
    final_lm_kwargs.update(**lm_kwargs)
    final_lm_kwargs.update(**lm_params)
    return final_lm_kwargs


# Todo: Ensure that we handle all clients equivently
# THis means we need a client parsing interface
def _run_lm(
    model: str,
    messages: list[Message],
    lm_kwargs: Dict[str, Any],
    _invocation_origin : str,
    exempt_from_tracking: bool,
    client: Optional[openai.Client] = None,
    _logging_color=None,
) -> Tuple[Union[lstr, Iterable[lstr]], Optional[Dict[str, Any]]]:
    """
    Helper function to run the language model with the provided messages and parameters.
    """
    # Todo: Decide if the client specified via the context amanger default registry is the shit or if the cliennt specified via lmp invocation args are the hing.
    client =   client or config.get_client_for(model)
    metadata = dict()
    if client is None:
        raise ValueError(f"No client found for model '{model}'. Ensure the model is registered using 'register_model' in 'config.py' or specify a client directly using the 'client' argument in the decorator or function call.")
    
    # todo: add suupport for streaming apis that dont give a final usage in the api
    model_result = client.chat.completions.create(
        model=model, messages=messages, stream=True, stream_options={"include_usage": True}, **lm_kwargs
    )

    
    choices_progress = defaultdict(list)
    n = lm_kwargs.get("n", 1)

    if config.verbose and not exempt_from_tracking:
        model_usage_logger_post_start(_logging_color, n)

    with model_usage_logger_post_intermediate(_logging_color, n) as _logger:
        for chunk in model_result:
            if chunk.usage:
                # Todo: is this a good decision.
                metadata = chunk.to_dict()
                continue
            for choice in chunk.choices:
                choices_progress[choice.index].append(choice)
                if config.verbose and choice.index == 0 and not exempt_from_tracking:
                    _logger(choice.delta.content)

    if config.verbose and not exempt_from_tracking:
        model_usage_logger_post_end()
    n_choices = len(choices_progress)

    tracked_results = [
        lstr(
            content="".join((choice.delta.content or "" for choice in choice_deltas)),
            # logits=( #
            #     np.concatenate([np.array(
            #         [c.logprob for c in choice.logprobs.content or []]
            #     ) for choice in choice_deltas])  # mypy type hinting is dogshit.
            # ),
            # Todo: Properly implement log probs.
            _origin_trace=_invocation_origin,
        )
        for _, choice_deltas in sorted(choices_progress.items(), key= lambda x: x[0],)
    ]

    return tracked_results[0] if n_choices == 1 else tracked_results, metadata



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
        wrapper.__ell_func__ = fn
        wrapper.__ell_lm = True
        wrapper.__ell_exempt_from_tracking = exempt_from_tracking
        if exempt_from_tracking:
            return wrapper
        else:
            return track(wrapper)
        

    return decorator



def track(fn: Callable) -> Callable:
    if hasattr(fn, "__ell_lm_kwargs__"):
        func_to_track = fn
        lm_kwargs = fn.__ell_lm_kwargs__
        lmp = True
    else:
        func_to_track = fn
        lm_kwargs = None
        lmp = False


    # see if it exists
    _name = func_to_track.__qualname__
    _time = time.time()
    _has_serialized_lmp = False
    

    @wraps(fn)
    def wrapper(*fn_args, get_invocation=False, **fn_kwargs) -> str:
        nonlocal _has_serialized_lmp
        assert (get_invocation and config.has_serializers) or not get_invocation, "In order to get an invocation, you must have a serializer and get_invocation must be True."

        
        invocation_id = "invocation-" + secrets.token_hex(16)

        _start_time = datetime.now()
        # get the prompt
        (result, invocation_kwargs, metadata) = (
            (fn(*fn_args, **fn_kwargs), None)
            if not lmp
            else fn(*fn_args, _invocation_origin=invocation_id, **fn_kwargs, )
            )
        latency_ms = (datetime.now() - _start_time).total_seconds() * 1000
        usage = metadata.get("usage", {})
        
            
            
        if config.has_serializers:
            if not _has_serialized_lmp:
                fn_closure, _uses = ell.util.closure.lexically_closured_source(func_to_track)


                for serializer in config.serializers:
                    # Compute commit messages if enabled
                    commit = None
                    lmps = serializer.get_lmps(name=_name)
                    version = 0
                    if any(lmp['lmp_id'] == func_to_track.__ell_hash__ for lmp in lmps):
                        continue

                    if len(lmps) > 0 :
                        lmps.sort(key=lambda x: x['created_at'], reverse=True)
                        latest_lmp = lmps[0]
        
        
                        version = (latest_lmp['version_number']) + 1
                        print(latest_lmp['version_number'], version)
                        if config.autocommit:
                        # Get the latest lmp
                        # sort by created at  
                            from ell.util.differ import write_commit_message_for_diff
                            commit = str(write_commit_message_for_diff(f"{latest_lmp['dependencies']}\n\n{latest_lmp['source']}", f"{fn_closure[1]}\n\n{fn_closure[0]}")[0])


                    serializer.write_lmp(
                        lmp_id=func_to_track.__ell_hash__,
                        name=_name,
                        created_at=datetime.now(),
                        source=fn_closure[0],
                        dependencies=fn_closure[1],
                        commit_message=(commit),
            
                        is_lmp=lmp,
                        lm_kwargs=(
                            (lm_kwargs)
                            if lm_kwargs
                            else None
                        ),
                        version_number=version,
                        uses=_uses,
                    )
                _has_serialized_lmp = True

            # Let's add an invocation
            invocation_params = dict(
                id=invocation_id,
                lmp_id=func_to_track.__ell_hash__,
                args=(fn_args),
                kwargs=(fn_kwargs),
                invocation_kwargs=invocation_kwargs,
                created_at=datetime.now(),
                latency_ms=latency_ms,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )

            
            invocation_converter = cattrs.Converter()
            consumes = set()
            
            def process_lstr(obj):
                consumes.update(obj._origin_trace)
                print("consuming", consumes )
                return invocation_converter.unstructure(dict(content=str(obj), **obj.__dict__, __lstr=True))

                
            invocation_converter.register_unstructure_hook(
                np.ndarray,
                lambda arr: arr.tolist()
            )
            invocation_converter.register_unstructure_hook(
                lstr,
                process_lstr
            )
            invocation_converter.register_unstructure_hook(
                set,
                lambda s: list(s)
            )
            invocation_converter.register_unstructure_hook(
                frozenset,
                lambda s: list(s)
            )
            
            
            cleaned_invocation_params = invocation_converter.unstructure(invocation_params)
            for serializer in config.serializers:
                print("wrinting invocation")
                serializer.write_invocation(**cleaned_invocation_params, consumes=consumes, result=result)
            
            invoc = invocation_params  # For compatibility with existing code

        if get_invocation:
            return result, invoc
        else:
            return result

    fn.__wrapper__  = wrapper
    wrapper.__ell_lm_kwargs__ = lm_kwargs
    wrapper.__ell_func__ = func_to_track
    wrapper.__ell_track = True

    return wrapper



