from functools import partial
from ell.configurator import config
import openai
from collections import defaultdict
from ell.lstr import lstr
from ell.types import LMP, LMPParams, Message, MessageOrDict


from typing import Any, Dict, Iterable, Optional, Tuple, Union

from ell.util.verbosity import model_usage_logger_post_end, model_usage_logger_post_intermediate, model_usage_logger_post_start
from ell.util._warnings import _no_api_key_warning

import logging
logger = logging.getLogger(__name__)

def _get_lm_kwargs(lm_kwargs: Dict[str, Any], lm_params: LMPParams) -> Dict[str, Any]:
    """
    Helper function to combine the default LM parameters with the provided LM parameters and the parameters passed to the LMP.
    """
    final_lm_kwargs = dict(**config.default_lm_params)
    final_lm_kwargs.update(**lm_kwargs)
    final_lm_kwargs.update(**lm_params)
    return final_lm_kwargs

def _get_messages(res: Union[str, list[MessageOrDict]], fn: LMP) -> list[Message]:
    """
    Helper function to convert the output of an LMP into a list of Messages.
    """
    if isinstance(res, str):
        return [
            Message(role="system", content=(fn.__doc__) or config.default_system_prompt),
            Message(role="user", content=res),
        ]
    else:
        assert isinstance(
            res, list
        ), "Need to pass a list of MessagesOrDict to the language model"
        return res


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
    name: str = None,
    tools: Optional[list[LMP]] = None,
) -> Tuple[Union[lstr, Iterable[lstr]], Optional[Dict[str, Any]]]:
    """
    Helper function to run the language model with the provided messages and parameters.
    """
    # Todo: Decide if the client specified via the context amanger default registry is the shit or if the cliennt specified via lmp invocation args are the hing.
    client =   client or config.get_client_for(model)
    metadata = dict()
    if client is None:
        raise ValueError(f"No client found for model '{model}'. Ensure the model is registered using 'register_model' in 'config.py' or specify a client directly using the 'client' argument in the decorator or function call.")
    
    if not client.api_key:
        raise RuntimeError(_no_api_key_warning(model, name, client, long=True, error=True))

    # todo: add suupport for streaming apis that dont give a final usage in the api
    # print(lm_kwargs)
    if lm_kwargs.get("response_format", False):
        model_call = client.beta.chat.completions.parse
        lm_kwargs.pop("stream", None)
        lm_kwargs.pop("stream_options", None)
    elif tools:
        model_call = client.chat.completions.create
        lm_kwargs["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": tool.__name__,
                    "description": tool.__doc__,
                    "parameters": tool.__ell_params_model__.model_json_schema()
                }
            } for tool in tools
        ]
        lm_kwargs["tool_choice"] = "auto"
        lm_kwargs.pop("stream", None)
        lm_kwargs.pop("stream_options", None)
    else:
        model_call = client.chat.completions.create
        lm_kwargs["stream"] = True
        lm_kwargs["stream_options"] = {"include_usage": True}

    # print(lm_kwargs)
    model_result = model_call(
        model=model, messages=messages, **lm_kwargs
    )
    streaming = lm_kwargs.get("stream", False)
    if not streaming:
        model_result = [model_result]

    choices_progress = defaultdict(list)
    n = lm_kwargs.get("n", 1)

    if config.verbose and not exempt_from_tracking:
        model_usage_logger_post_start(_logging_color, n)

    with model_usage_logger_post_intermediate(_logging_color, n) as _logger:
        for chunk in model_result:
            if hasattr(chunk, "usage") and chunk.usage:
                # Todo: is this a good decision.
                metadata = chunk.to_dict()
                
                if streaming:
                    continue
            
            for choice in chunk.choices:
                choices_progress[choice.index].append(choice)
                if config.verbose and choice.index == 0 and not exempt_from_tracking:
                    # print(choice, streaming)
                    _logger(choice.delta.content if streaming else 
                        choice.message.content or getattr(choice.message, "refusal", ""), is_refusal=getattr(choice.message, "refusal", False) if not streaming else False)

    if config.verbose and not exempt_from_tracking:
        model_usage_logger_post_end()
    n_choices = len(choices_progress)

    print(choice.message.tool_calls)
    tracked_results = [
        lstr(
            content="".join((choice.delta.content or "" for choice in choice_deltas)) if streaming else choice.message.content,
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