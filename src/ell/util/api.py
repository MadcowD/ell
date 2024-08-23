from functools import partial
import json

# import anthropic
from ell.configurator import config
import openai
from collections import defaultdict
from ell._lstr import _lstr
from ell.types import LMP, LMPParams, Message, MessageContentBlock, MessageOrDict, ToolCall


from typing import Any, Dict, Iterable, Optional, Tuple, Union

from ell.util.verbosity import model_usage_logger_post_end, model_usage_logger_post_intermediate, model_usage_logger_post_start
from ell.util._warnings import _no_api_key_warning

import logging
logger = logging.getLogger(__name__)


def process_messages_for_client(messages: list[Message], client: Any):
    if isinstance(client, openai.Client):
        return [
            message.to_openai_message()
         for message in messages]
    # elif isinstance(client, anthropic.Anthropic):
        # return messages
    # XXX: or some such.


def call(
    *, 
    model: str,
    messages: list[Message],
    lm_kwargs: Dict[str, Any],
    tools: Optional[list[LMP]] = None,
    client: Optional[openai.Client] = None,
    _invocation_origin : str,
    _exempt_from_tracking: bool,
    _logging_color=None,
    _name: str = None,
) -> Tuple[Union[_lstr, Iterable[_lstr]], Optional[Dict[str, Any]]]:
    """
    Helper function to run the language model with the provided messages and parameters.
    """
    # Todo: Decide if the client specified via the context amanger default registry is the shit or if the cliennt specified via lmp invocation args are the hing.
    client =   client or config.get_client_for(model)
    metadata = dict()
    if client is None:
        raise ValueError(f"No client found for model '{model}'. Ensure the model is registered using 'register_model' in 'config.py' or specify a client directly using the 'client' argument in the decorator or function call.")
    
    if not client.api_key:
        raise RuntimeError(_no_api_key_warning(model, _name, client, long=True, error=True))

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
    
    client_safe_messages_messages = process_messages_for_client(messages, client)
    # print(lm_kwargs)
    model_result = model_call(
        model=model, messages=client_safe_messages_messages, **lm_kwargs
    )
    streaming = lm_kwargs.get("stream", False)
    if not streaming:
        model_result = [model_result]

    choices_progress = defaultdict(list)
    n = lm_kwargs.get("n", 1)

    if config.verbose and not _exempt_from_tracking:
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
                if config.verbose and choice.index == 0 and not _exempt_from_tracking:
                    # print(choice, streaming)
                    _logger(choice.delta.content if streaming else 
                        choice.message.content or getattr(choice.message, "refusal", ""), is_refusal=getattr(choice.message, "refusal", False) if not streaming else False)

    if config.verbose and not _exempt_from_tracking:
        model_usage_logger_post_end()
    n_choices = len(choices_progress)

    # coerce the streaming into a final message type
    tracked_results = []
    for _, choice_deltas in sorted(choices_progress.items(), key=lambda x: x[0]):
        content = []
        
        # Handle text content
        if streaming:
            text_content = "".join((choice.delta.content or "" for choice in choice_deltas))
            if text_content:
                content.append(MessageContentBlock(
                    text=_lstr(content=text_content, _origin_trace=_invocation_origin)
                ))
        else:
            choice = choice_deltas[0].message
            if choice.content:
                content.append(MessageContentBlock(
                    text=_lstr(content=choice.content, _origin_trace=_invocation_origin)
                ))
        
        # Handle tool calls
        if not streaming and hasattr(choice, 'tool_calls'):
            for tool_call in choice.tool_calls or []:
                matching_tool = None
                for tool in tools:
                    if tool.__name__ == tool_call.function.name:
                        matching_tool = tool
                        break
                
                if matching_tool:
                    params = matching_tool.__ell_params_model__(**json.loads(tool_call.function.arguments))
                    content.append(MessageContentBlock(
                        tool_call=ToolCall(tool=matching_tool, params=params)
                    ))
        
        tracked_results.append(Message(
            role=choice.role if not streaming else choice_deltas[0].delta.role,
            content=content
        ))
    
    api_params = dict(model=model, messages=client_safe_messages_messages, lm_kwargs=lm_kwargs)
    
    return tracked_results[0] if n_choices == 1 else tracked_results, api_params, metadata