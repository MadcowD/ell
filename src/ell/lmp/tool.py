from functools import wraps
from typing import Optional

from pydantic import Field, create_model
from pydantic.fields import FieldInfo
from ell.lmp.track import track
# from ell.types import ToolFunction, InvocableTool, ToolParams
# from ell.util.verbosity import compute_color, tool_usage_logger_pre
from ell.configurator import config
from ell.types import LMPType
import inspect

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
            # tool_params: ToolParams = {},
            invocation_kwargs=False,
            **fn_kwargs
        ):
            # assert exempt_from_tracking or _invocation_origin is not None, "Invocation origin is required when using a tracked Tool"
            # Do nice logging hooks here.

            if config.verbose and not exempt_from_tracking:
                pass
                # tool_usage_logger_pre(fn, fn_args, fn_kwargs, name, color)

            result = fn(*fn_args, **fn_kwargs)

            _invocation_kwargs = dict(tool_kwargs=tool_kwargs)
            
            # Here you might want to add logic for tracking the tool usage
            # Similar to how it's done in the lm decorator

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
            else:
                fields[param_name] = (annotation, default)

        # 3. Create the Pydantic model
        model_name = f"{fn.__name__.capitalize()}Params"
        ParamsModel = create_model(model_name, **fields)
        
        # Attach the Pydantic model to the wrapper function
        wrapper.__ell_params_model__ = ParamsModel

        # handle tracking last.
        if exempt_from_tracking:
            return wrapper
        else:
            return track(wrapper)

    return decorator
