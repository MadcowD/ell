from ell.configurator import config
from ell.lmp._track import _track
from ell.types._lstr import _lstr
from ell.types import Message, ContentBlock
from ell.types.message import LMP, InvocableLM, LMPParams, MessageOrDict, _lstr_generic
from ell.types.studio import LMPType
from ell.util._warnings import _warnings
from ell.util.api import  call
from ell.util.verbosity import compute_color, model_usage_logger_pre


import openai

from functools import wraps
from typing import Any, Dict, Optional, List, Callable, Union

def complex(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, tools: Optional[List[Callable]] = None, post_callback: Optional[Callable] = None, **api_params):
    """
    A sophisticated language model programming decorator for complex LLM interactions.

    This decorator transforms a function into a Language Model Program (LMP) capable of handling
    multi-turn conversations, tool usage, and various output formats. It's designed for advanced
    use cases where full control over the LLM's capabilities is needed.

    :param model: The name or identifier of the language model to use.
    :type model: str
    :param client: An optional OpenAI client instance. If not provided, a default client will be used.
    :type client: Optional[openai.Client]
    :param tools: A list of tool functions that can be used by the LLM. Only available for certain models.
    :type tools: Optional[List[Callable]]
    :param response_format: The response format for the LLM. Only available for certain models.
    :type response_format: Optional[Dict[str, Any]]
    :param n: The number of responses to generate for the LLM. Only available for certain models.
    :type n: Optional[int]
    :param temperature: The temperature parameter for controlling the randomness of the LLM.
    :type temperature: Optional[float]
    :param max_tokens: The maximum number of tokens to generate for the LLM.
    :type max_tokens: Optional[int]
    :param top_p: The top-p sampling parameter for controlling the diversity of the LLM.
    :type top_p: Optional[float]
    :param frequency_penalty: The frequency penalty parameter for controlling the LLM's repetition.
    :type frequency_penalty: Optional[float]
    :param presence_penalty: The presence penalty parameter for controlling the LLM's relevance.
    :type presence_penalty: Optional[float]
    :param stop: The stop sequence for the LLM.
    :type stop: Optional[List[str]]
    :param exempt_from_tracking: If True, the LMP usage won't be tracked. Default is False.
    :type exempt_from_tracking: bool
    :param post_callback: An optional function to process the LLM's output before returning.
    :type post_callback: Optional[Callable]
    :param api_params: Additional keyword arguments to pass to the underlying API call.
    :type api_params: Any

    :return: A decorator that can be applied to a function, transforming it into a complex LMP.
    :rtype: Callable

    Functionality:

    1. Advanced LMP Creation:
       - Supports multi-turn conversations and stateful interactions.
       - Enables tool usage within the LLM context.
       - Allows for various output formats, including structured data and function calls.

    2. Flexible Input Handling:
       - Can process both single prompts and conversation histories.
       - Supports multimodal inputs (text, images, etc.) in the prompt.

    3. Comprehensive Integration:
       - Integrates with ell's tracking system for monitoring LMP versions, usage, and performance.
       - Supports various language models and API configurations.

    4. Output Processing:
       - Can return raw LLM outputs or process them through a post-callback function.
       - Supports returning multiple message types (e.g., text, function calls, tool results).

    Usage Modes and Examples:

    1. Basic Prompt:

    .. code-block:: python

       @ell.complex(model="gpt-4")
       def generate_story(prompt: str) -> List[Message]:
           '''You are a creative story writer''' # System prompt
           return [
               ell.user(f"Write a short story based on this prompt: {prompt}")
           ]

       story : ell.Message = generate_story("A robot discovers emotions") 
       print(story.text)  # Access the text content of the last message

    2. Multi-turn Conversation:

    .. code-block:: python

       @ell.complex(model="gpt-4")
       def chat_bot(message_history: List[Message]) -> List[Message]:
           return [
               ell.system("You are a helpful assistant."),
           ] + message_history

       conversation = [
           ell.user("Hello, who are you?"),
           ell.assistant("I'm an AI assistant. How can I help you today?"),
           ell.user("Can you explain quantum computing?")
       ]
       response : ell.Message = chat_bot(conversation)
       print(response.text)  # Print the assistant's response

    3. Tool Usage:

    .. code-block:: python

       @ell.tool()
       def get_weather(location: str) -> str:
           # Implementation to fetch weather
           return f"The weather in {location} is sunny."

       @ell.complex(model="gpt-4", tools=[get_weather])
       def weather_assistant(message_history: List[Message]) -> List[Message]:
           return [
               ell.system("You are a weather assistant. Use the get_weather tool when needed."),
           ] + message_history

       conversation = [
           ell.user("What's the weather like in New York?")
       ]
       response : ell.Message = weather_assistant(conversation)
       
       if response.tool_calls:
           tool_results = response.call_tools_and_collect_as_message()
           print("Tool results:", tool_results.text)
           
           # Continue the conversation with tool results
           final_response = weather_assistant(conversation + [response, tool_results])
           print("Final response:", final_response.text)

    4. Structured Output:

    .. code-block:: python

       from pydantic import BaseModel

       class PersonInfo(BaseModel):
           name: str
           age: int

       @ell.complex(model="gpt-4", response_format=PersonInfo)
       def extract_person_info(text: str) -> List[Message]:
           return [
               ell.system("Extract person information from the given text."),
               ell.user(text)
           ]

       text = "John Doe is a 30-year-old software engineer."
       result : ell.Message = extract_person_info(text)
       person_info = result.structured[0]
       print(f"Name: {person_info.name}, Age: {person_info.age}")

    5. Multimodal Input:

    .. code-block:: python

       @ell.complex(model="gpt-4-vision-preview")
       def describe_image(image: PIL.Image.Image) -> List[Message]:
           return [
               ell.system("Describe the contents of the image in detail."),
               ell.user([
                   ContentBlock(text="What do you see in this image?"),
                   ContentBlock(image=image)
               ])
           ]

       image = PIL.Image.open("example.jpg")
       description = describe_image(image)
       print(description.text)

    6. Parallel Tool Execution:

    .. code-block:: python

       @ell.complex(model="gpt-4", tools=[tool1, tool2, tool3])
       def parallel_assistant(message_history: List[Message]) -> List[Message]:
           return [
               ell.system("You can use multiple tools in parallel."),
           ] + message_history

       response = parallel_assistant([ell.user("Perform tasks A, B, and C simultaneously.")])
       if response.tool_calls:
           tool_results : ell.Message = response.call_tools_and_collect_as_message(parallel=True, max_workers=3)
           print("Parallel tool results:", tool_results.text)

    Helper Functions for Output Processing:

    - response.text: Get the full text content of the last message.
    - response.text_only: Get only the text content, excluding non-text elements.
    - response.tool_calls: Access the list of tool calls in the message.
    - response.tool_results: Access the list of tool results in the message.
    - response.structured: Access structured data outputs.
    - response.call_tools_and_collect_as_message(): Execute tool calls and collect results.
    - Message(role="user", content=[...]).to_openai_message(): Convert to OpenAI API format.

    Notes:

    - The decorated function should return a list of Message objects.
    - For tool usage, ensure that tools are properly decorated with @ell.tool().
    - When using structured outputs, specify the response_format in the decorator.
    - The complex decorator supports all features of simpler decorators like @ell.simple.
    - Use helper functions and properties to easily access and process different types of outputs.

    See Also:

    - ell.simple: For simpler text-only LMP interactions.
    - ell.tool: For defining tools that can be used within complex LMPs.
    - ell.studio: For visualizing and analyzing LMP executions.
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
            invocation_api_params=False,
            **fn_kwargs,
        ) -> _lstr_generic:
            res = prompt(*fn_args, **fn_kwargs)

            assert exempt_from_tracking or _invocation_origin is not None, "Invocation origin is required when using a tracked LMP"
            messages = _get_messages(res, prompt)

            if config.verbose and not exempt_from_tracking: model_usage_logger_pre(prompt, fn_args, fn_kwargs, "notimplemented", messages, color)

            (result, _api_params, metadata) = call(model=model, messages=messages, api_params={**config.default_lm_params, **api_params, **lm_params}, client=client or default_client_from_decorator, _invocation_origin=_invocation_origin, _exempt_from_tracking=exempt_from_tracking, _logging_color=color, _name=prompt.__name__, tools=tools)
        
            result = post_callback(result) if post_callback else result
            

            return result, api_params, metadata


  
        # TODO: # we'll deal with type safety here later
        model_call.__ell_api_params__ = api_params
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
        ), "Need to pass a list of Messages to the language model"
        return prompt_ret
