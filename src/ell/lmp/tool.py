from functools import wraps
import json
from typing import Any, Callable, Optional

from pydantic import Field, create_model
from pydantic.fields import FieldInfo
from ell.lmp._track import _track
# from ell.types import ToolFunction, InvocableTool, ToolParams
# from ell.util.verbosity import compute_color, tool_usage_logger_pre
from ell.configurator import config
from ell.types._lstr import _lstr
from ell.types.studio import LMPType
import inspect

from ell.types.message import ContentBlock, InvocableTool, ToolResult, coerce_content_list



def tool(*, exempt_from_tracking: bool = False, **tool_kwargs):
    """
    Defines a tool for use in language model programs (LMPs) that support tool use.

    This decorator wraps a function, adding metadata and handling for tool invocations.
    It automatically extracts the tool's description and parameters from the function's
    docstring and type annotations, creating a structured representation for LMs to use.

    :param exempt_from_tracking: If True, the tool usage won't be tracked. Default is False.
    :type exempt_from_tracking: bool
    :param tool_kwargs: Additional keyword arguments for tool configuration.
    :return: A wrapped version of the original function, usable as a tool by LMs.
    :rtype: Callable

    Requirements:

    - Function must have fully typed arguments (Pydantic-serializable).
    - Return value must be one of: str, JSON-serializable object, Pydantic model, or List[ContentBlock].
    - All parameters must have type annotations.
    - Complex types should be Pydantic models.
    - Function should have a descriptive docstring.
    - Can only be used in LMPs with @ell.complex decorators

    Functionality:

    1. Metadata Extraction:
       - Uses function docstring as tool description.
       - Extracts parameter info from type annotations and docstring.
       - Creates a Pydantic model for parameter validation and schema generation.

    2. Integration with LMs:
       - Can be passed to @ell.complex decorators.
       - Provides structured tool information to LMs.

    3. Invocation Handling:
       - Manages tracking, logging, and result processing.
       - Wraps results in appropriate types (e.g., _lstr) for tracking.

    Usage Modes:

    1. Normal Function Call:
       - Behaves like a regular Python function.
       - Example: result = my_tool(arg1="value", arg2=123)

    2. LMP Tool Call:
       - Used within LMPs or with explicit _tool_call_id.
       - Returns a ToolResult object.
       - Example: result = my_tool(arg1="value", arg2=123, _tool_call_id="unique_id")

    Result Coercion:

    - String → ContentBlock(text=result)
    - Pydantic BaseModel → ContentBlock(parsed=result)
    - List[ContentBlock] → Used as-is
    - Other types → ContentBlock(text=json.dumps(result))

    Example::

        @ell.tool()
        def create_claim_draft(
            claim_details: str,
            claim_type: str,
            claim_amount: float,
            claim_date: str = Field(description="Date format: YYYY-MM-DD")
        ) -> str:
            '''Create a claim draft. Returns the created claim ID.'''
            return "12345"

        # For use in a complex LMP:
        @ell.complex(model="gpt-4", tools=[create_claim_draft], temperature=0.1)
        def insurance_chatbot(message_history: List[Message]) -> List[Message]:
            # Chatbot implementation...

        x = insurance_chatbot([
            ell.user("I crashed my car into a tree."),
            ell.assistant("I'm sorry to hear that. Can you provide more details?"),
            ell.user("The car is totaled and I need to file a claim. Happened on 2024-08-01. total value is like $5000")
        ]) 
        print(x)
        '''ell.Message(content=[
            ContentBlock(tool_call(
                tool_call_id="asdas4e",
                tool_fn=create_claim_draft,
                input=create_claim_draftParams({
                    claim_details="The car is totaled and I need to file a claim. Happened on 2024-08-01. total value is like $5000",
                    claim_type="car",
                    claim_amount=5000,
                    claim_date="2024-08-01"
                })
            ))
        ], role='assistant')'''
        
        if x.tool_calls:
            next_user_message = response_message.call_tools_and_collect_as_message()
            # This actually calls create_claim_draft
            print(next_user_message)
            '''
            ell.Message(content=[
                ContentBlock(tool_result=ToolResult(
                    tool_call_id="asdas4e",
                    result=[ContentBlock(text="12345")]
                ))
            ], role='user')
            '''
            y = insurance_chatbot(message_history + [x, next_user_message])
            print(y)
            '''
            ell.Message("I've filed that for you!", role='assistant')
            '''

    Note:
    - Tools are integrated into LMP calls via the 'tools' parameter in @ell.complex.
    - LMs receive structured tool information, enabling understanding and usage within the conversation context.
    """
    def tool_decorator(fn: Callable[..., Any]) -> InvocableTool:
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

            _invocation_api_params = dict(tool_kwargs=tool_kwargs)
            
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
                    if c.parsed:
                        # Warning: Formatted response in tool result will be converted to text
                        # TODO: Logging needs to produce not print.
                        print(f"Warning: Formatted response in tool result will be converted to text. Original: {c.parsed}")
                        c.text = _lstr(c.parsed.model_dump_json(), _origin_trace=_invocation_origin)
                        c.parsed = None
                    assert not c.audio, "Audio in tool result"
                return ToolResult(tool_call_id=_tool_call_id, result=content_results), _invocation_api_params, {}
            else:
                return result, _invocation_api_params, {}


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
            ret = wrapper
        else:
            ret=  _track(wrapper)

        # Helper function to get the Pydantic model for the tool
        def get_params_model():
            return wrapper.__ell_params_model__
        
        # Attach the helper function to the wrapper
        wrapper.get_params_model = get_params_model
        ret.get_params_model = get_params_model
        return ret

    return tool_decorator
