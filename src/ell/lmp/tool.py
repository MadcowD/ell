from functools import wraps
import json
from typing import Optional

from pydantic import Field, create_model
from pydantic.fields import FieldInfo
from ell.lmp._track import _track
# from ell.types import ToolFunction, InvocableTool, ToolParams
# from ell.util.verbosity import compute_color, tool_usage_logger_pre
from ell.configurator import config
from ell._lstr import _lstr
from ell.types.lmp import LMPType
import inspect

from ell.types.message import ContentBlock, ToolResult, coerce_content_list

def tool(*, exempt_from_tracking: bool = False, **tool_kwargs):
    """
    Defines a tool that can be used by language models.

    This is a decorator that can be applied to any ToolFunction type.
    """
    def decorator(fn: "ToolFunction") -> "InvocableTool":
        # color = compute_color(fn)
        _under_fn = fn

        @wraps(fn)
        def wrapper(
            *fn_args,
            _invocation_origin: str = None,
            _tool_call_id: str = None,
            **fn_kwargs
        ):
            
            #XXX: Post release, we need to wrap all tool arguments in type primitives for tracking I guess or change that tool makes the tool function inoperable.
            #XXX: Most people are not going to manually try and call the tool without a type primitive and if they do it will most likely be wrapped with l strs.

            
            # assert exempt_from_tracking or _invocation_origin is not None, "Invocation origin is required when using a tracked Tool"
            # Do nice logging hooks here.

            if config.verbose and not exempt_from_tracking:
                pass
                # tool_usage_logger_pre(fn, fn_args, fn_kwargs, name, color)

            result = fn(*fn_args, **fn_kwargs)

            _invocation_kwargs = dict(tool_kwargs=tool_kwargs)
            
            # Here you might want to add logic for tracking the tool usage
            # Similar to how it's done in the lm decorator # Use _invocation_origin

            if isinstance(result, str) and _invocation_origin:
                result = _lstr(result, _origin_trace=_invocation_origin)

            #XXX: This _tool_call_id thing is a hack. Tracking should happen via params in the api
            if _tool_call_id:
                try:
                    content_results = coerce_content_list(result)
                except ValueError as e:
                    # XXX: TODO: MOVE TRACKING CODE TO _TRACK AND OUT OF HERE AND API.
                    content_results = [ContentBlock(text=_lstr(json.dumps(result), _origin_trace=_invocation_origin))]
                
                # TODO: poolymorphic validation here is important (cant have tool_call or formatted_response in the result)
                # XXX: Should we put this coercion here or in the tool call/result area.
                for c in content_results:
                    assert not c.tool_call, "Tool call in tool result"
                    # assert not c.formatted_response, "Formatted response in tool result"
                    if c.formatted_response:
                        # Warning: Formatted response in tool result will be converted to text
                        # TODO: Logging needs to produce not print.
                        print(f"Warning: Formatted response in tool result will be converted to text. Original: {c.formatted_response}")
                        c.text = _lstr(c.formatted_response.model_dump_json(), _origin_trace=_invocation_origin)
                        c.formatted_response = None
                    assert not c.audio, "Audio in tool result"
                return ToolResult(tool_call_id=_tool_call_id, result=content_results), _invocation_kwargs, {}
            else:
                return result, _invocation_kwargs, {}


        wrapper.__ell_tool_kwargs__ = tool_kwargs
        wrapper.__ell_func__ = _under_fn
        wrapper.__ell_type__ = LMPType.TOOL
        wrapper.__ell_exempt_from_tracking = exempt_from_tracking

        # Construct the pydantic mdoel for the _under_fn's function signature parameters.
        # 1. Get the function signature.
        
        sig = inspect.signature(fn)
        
        # Create a Pydantic model from the function signature
        # 2. Create a dictionary of field definitions for the Pydantic model
        fields = {}
        for param_name, param in sig.parameters.items():
            # Skip *args and **kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            
            # Determine the type annotation
            if param.annotation == inspect.Parameter.empty:
                raise ValueError(f"Parameter {param_name} has no type annotation, and cannot be converted into a tool schema for OpenAI and other provisders. Should OpenAI produce a string or an integer, etc, for this parameter?")
            annotation = param.annotation 
            
            # Determine the default value
            default = param.default
            
            # Check if the parameter has a Field with description
            if isinstance(param.default, FieldInfo):
                field = param.default
                fields[param_name] = (annotation, field)
            elif param.default != inspect.Parameter.empty:
                fields[param_name] = (annotation, param.default)
            else:
                # If no default value, use Field without default
                fields[param_name] = (annotation, Field(...))

        # 3. Create the Pydantic model
        model_name = f"{fn.__name__}Params"
        ParamsModel = create_model(model_name, **fields)
        
        # Attach the Pydantic model to the wrapper function
        wrapper.__ell_params_model__ = ParamsModel

        # handle tracking last.
        if exempt_from_tracking:
            return wrapper
        else:
            return _track(wrapper)

    return decorator
