from functools import partial
import os

from ell.configurator import config

from collections import defaultdict
from ell.types._lstr import _lstr
from ell.types import Message, ContentBlock, ToolCall

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, Type
from ell.types.message import LMP, LMPParams, MessageOrDict

from ell.util.verbosity import model_usage_logger_post_end, model_usage_logger_post_intermediate, model_usage_logger_post_start
from ell.util._warnings import _no_api_key_warning
from ell.provider import APICallResult, Provider

import logging
logger = logging.getLogger(__name__)

def call(
    *, 
    model: str,
    messages: list[Message],
    api_params: Dict[str, Any],
    tools: Optional[list[LMP]] = None,
    client: Optional[Any] = None,
    _invocation_origin: str,
    _exempt_from_tracking: bool,
    _logging_color: Optional[str] = None,
    _name: Optional[str] = None,
) -> Tuple[Union[Message, List[Message]], Dict[str, Any], Dict[str, Any]]:
    """
    Helper function to run the language model with the provided messages and parameters.
    """
    if not client:
        client, was_fallback = config.get_client_for(model)
        if not client and not was_fallback:
            raise RuntimeError(_no_api_key_warning(model, _name, '', long=True, error=True))
    
    if client is None:
        raise ValueError(f"No client found for model '{model}'. Ensure the model is registered using 'register_model' in 'config.py' or specify a client directly using the 'client' argument in the decorator or function call.")
    
    if client.__class__.__module__ == 'cohere.client':
        api_key = os.environ.get("COHERE_API_KEY") or os.environ.get("CO_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable is not set")
    elif not client.api_key:
        raise RuntimeError(_no_api_key_warning(model, _name, client, long=True, error=True))
        
    provider_class: Type[Provider] = config.get_provider_for(client)

    if provider_class is None:
        raise ValueError(f"No provider found for client type {type(client)}. Ensure the provider is registered using 'register_provider'.")

    call_result = provider_class.call_model(client, model, messages, api_params, tools)
    
    if config.verbose and not _exempt_from_tracking:
        model_usage_logger_post_start(_logging_color, call_result.actual_n)

    with model_usage_logger_post_intermediate(_logging_color, call_result.actual_n) as _logger:
        tracked_results, metadata = provider_class.process_response(call_result, _invocation_origin, _logger if config.verbose and not _exempt_from_tracking else None, tools)
        
    if config.verbose and not _exempt_from_tracking:
        model_usage_logger_post_end()

    return (tracked_results[0] if len(tracked_results) == 1 else tracked_results), call_result.final_call_params, metadata