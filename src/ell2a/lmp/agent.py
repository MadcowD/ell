from functools  import wraps
import json
from typing import Any, Callable, Optional

from pydantic import Field, create_model
from pydantic.fields import FieldInfo
from ell2a.lmp._track import _track
# from ell2a.types import AgentFunction, InvocableAgent, AgentParams
# from ell2a.util.verbosity import compute_color, agent_usage_logger_pre
from ell2a.configurator import config
from ell2a.types._lstr import _lstr
from ell2a.types.studio import LMPType
import inspect

from ell2a.types.message import ContentBlock, InvocableAgent, AgentResult, to_content_blocks


def agent(*, exempt_from_tracking: bool = False, **agent_kwargs):
    def agent_decorator(fn: Callable[..., Any]) -> InvocableAgent:
        _under_fn = fn

        @wraps(fn)
        def wrapper(
            *fn_args,
            _invocation_origin: str = None,
            _agent_call_id: str = None,
            **fn_kwargs
        ):
            # XXX: Post release, we need to wrap all agent arguments in type primitives for tracking I guess or change that agent makes the agent function inoperable.
            # XXX: Most people are not going to manually try and call the agent without a type primitive and if they do it will most likely be wrapped with l strs.

            if config.verbose and not exempt_from_tracking:
                pass
                # agent_usage_logger_pre(fn, fn_args, fn_kwargs, name, color)

            result = fn(*fn_args, **fn_kwargs)

            _invocation_api_params = dict(agent_kwargs=agent_kwargs)

            # Here you might want to add logic for tracking the agent usage
            # Similar to how it's done in the lm decorator # Use _invocation_origin

            if isinstance(result, str) and _invocation_origin:
                result = _lstr(result, origin_trace=_invocation_origin)

            # XXX: This _agent_call_id thing is a hack. Tracking should happen via params in the api
            # So if you call wiuth a _agent_callId
            if _agent_call_id:
                # XXX: TODO: MOVE TRACKING CODE TO _TRACK AND OUT OF HERE AND API.
                try:
                    if isinstance(result, ContentBlock):
                        content_results = [result]
                    elif isinstance(result, list) and all(isinstance(c, ContentBlock) for c in result):
                        content_results = result
                    else:
                        content_results = [ContentBlock(text=_lstr(json.dumps(
                            result, ensure_ascii=False), origin_trace=_invocation_origin))]
                except TypeError as e:
                    raise TypeError(f"Failed to convert agent use result to ContentBlock: {e}. Agents must return json serializable objects. or a list of ContentBlocks.")
                # XXX: Need to support images and other content types somehow. We should look for images inside of the the result and then go from there.
                # try:
                #     content_results = coerce_content_list(result)
                # except ValueError as e:

                # TODO: poolymorphic validation here is important (cant have agent_call or formatted_response in the result)
                # XXX: Should we put this coercion here or in the agent call/result area.
                for c in content_results:
                    assert not c.agent_call, "Agent call in agent result"
                    # assert not c.formatted_response, "Formatted response in agent result"
                    if c.parsed:
                        # Warning: Formatted response in agent result will be converted to text
                        # TODO: Logging needs to produce not print.
                        print(f"Warning: Formatted response in agent result will be converted to text. Original: {c.parsed}")
                        c.text = _lstr(c.parsed.model_dump_json(),
                                       origin_trace=_invocation_origin)
                        c.parsed = None
                    assert not c.audio, "Audio in agent result"
                return AgentResult(agent_call_id=_agent_call_id, result=content_results), _invocation_api_params, {}
            else:
                return result, _invocation_api_params, {}

        wrapper.__ell2a_agent_kwargs__ = agent_kwargs
        wrapper.__ell2a_func__ = _under_fn
        wrapper.__ell2a_type__ = LMPType.AGENT
        wrapper.__ell2a_exempt_from_tracking = exempt_from_tracking

        # Construct the pydantic mdoel for the _under_fn's function signature parameters.
        # 1. Get the function signature.

        sig = inspect.signature(fn)

        # 2. Create a dictionary of field definitions for the Pydantic model
        fields = {}
        for param_name, param in sig.parameters.items():
            # Skip *args and **kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Determine the type annotation
            if param.annotation == inspect.Parameter.empty:
                raise ValueError(f"Parameter {param_name} has no type annotation, and cannot be converted into a agent schema for OpenAI and other provisders. Should OpenAI produce a string or an integer, etc, for this parameter?")
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
        model_name = f"{fn.__name__}"
        ParamsModel = create_model(model_name, **fields)

        # Attach the Pydantic model to the wrapper function
        wrapper.__ell2a_params_model__ = ParamsModel

        # handle tracking last.
        if exempt_from_tracking:
            ret = wrapper
        else:
            ret = _track(wrapper)

        # Helper function to get the Pydantic model for the agent
        def get_params_model():
            return wrapper.__ell2a_params_model__

        # Attach the helper function to the wrapper
        wrapper.get_params_model = get_params_model
        ret.get_params_model = get_params_model
        return ret

    return agent_decorator


agent.__doc__ = """Defines a agent for use in language model programs (LMPs) that support agent use.

This decorator wraps a function, adding metadata and handling for agent invocations.
It automatically extracts the agent's description and parameters from the function's
docstring and type annotations, creating a structured representation for LMs to use.

:param exempt_from_tracking: If True, the agent usage won't be tracked. Default is False.
:type exempt_from_tracking: bool
:param agent_kwargs: Additional keyword arguments for agent configuration.
:return: A wrapped version of the original function, usable as a agent by LMs.
:rtype: Callable

Requirements:

- Function must have fully typed arguments (Pydantic-serializable).
- Return value must be one of: str, JSON-serializable object, Pydantic model, or List[ContentBlock].
- All parameters must have type annotations.
- Complex types should be Pydantic models.
- Function should have a descriptive docstring.
- Can only be used in LMPs with @ell2a.complex decorators

Functionality:

1. Metadata Extraction:
    - Uses function docstring as agent description.
    - Extracts parameter info from type annotations and docstring.
    - Creates a Pydantic model for parameter validation and schema generation.

2. Integration with LMs:
    - Can be passed to @ell2a.complex decorators.
    - Provides structured agent information to LMs.

3. Invocation Handling:
    - Manages tracking, logging, and result processing.
    - Wraps results in appropriate types (e.g., _lstr) for tracking.

Usage Modes:

1. Normal Function Call:
    - Behaves like a regular Python function.
    - Example: result = my_agent(arg1="value", arg2=123)

2. LMP Agent Call:
    - Used within LMPs or with explicit _agent_call_id.
    - Returns a AgentResult object.
    - Example: result = my_agent(arg1="value", arg2=123, _agent_call_id="unique_id")

Result Coercion:

- String → ContentBlock(text=result)
- Pydantic BaseModel → ContentBlock(parsed=result)
- List[ContentBlock] → Used as-is
- Other types → ContentBlock(text=json.dumps(result))

Example::

    @ell2a.agent()
    def create_claim_draft(
        claim_details: str,
        claim_type: str,
        claim_amount: float,
        claim_date: str = Field(description="Date format: YYYY-MM-DD")
    ) -> str:
        '''Create a claim draft. Returns the created claim ID.'''
        return "12345"

    # For use in a complex LMP:
    @ell2a.complex(model="gpt-4", agents=[create_claim_draft], temperature=0.1)
    def insurance_chatbot(message_history: List[Message]) -> List[Message]:
        # Chatbot implementation...

    x = insurance_chatbot([
        ell2a.user("I crashed my car into a tree."),
        ell2a.assistant("I'm sorry to hear that. Can you provide more details?"),
        ell2a.user("The car is totaled and I need to file a claim. Happened on 2024-08-01. total value is like $5000")
    ])
    print(x)
    '''ell2a.Message(content=[
        ContentBlock(agent_call(
            agent_call_id="asdas4e",
            agent_fn=create_claim_draft,
            input=create_claim_draftParams({
                claim_details="The car is totaled and I need to file a claim. Happened on 2024-08-01. total value is like $5000",
                claim_type="car",
                claim_amount=5000,
                claim_date="2024-08-01"
            })
        ))
    ], role='assistant')'''

    if x.agent_calls:
        next_user_message = response_message.call_agents_and_collect_as_message()
        # This actually calls create_claim_draft
        print(next_user_message)
        '''
        ell2a.Message(content=[
            ContentBlock(agent_result=AgentResult(
                agent_call_id="asdas4e",
                result=[ContentBlock(text="12345")]
            ))
        ], role='user')
        '''
        y = insurance_chatbot(message_history + [x, next_user_message])
        print(y)
        '''
        ell2a.Message("I've filed that for you!", role='assistant')
        '''

Note:
- Agents are integrated into LMP calls via the 'agents' parameter in @ell2a.complex.
- LMs receive structured agent information, enabling understanding and usage within the conversation context.
    """
