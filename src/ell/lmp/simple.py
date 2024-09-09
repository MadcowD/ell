from functools import wraps
from typing import Optional

import openai
from ell.lmp.complex import complex


def simple(model: str, client: Optional[openai.Client] = None,  exempt_from_tracking=False, **api_params):
    """
    The fundamental unit of language model programming in ell.

    This decorator simplifies the process of creating Language Model Programs (LMPs) 
    that return text-only outputs from language models, while supporting multimodal inputs.
    It wraps the more complex 'complex' decorator, providing a streamlined interface for common use cases.

    :param model: The name or identifier of the language model to use.
    :type model: str
    :param client: An optional OpenAI client instance. If not provided, a default client will be used.
    :type client: Optional[openai.Client]
    :param exempt_from_tracking: If True, the LMP usage won't be tracked. Default is False.
    :type exempt_from_tracking: bool
    :param api_params: Additional keyword arguments to pass to the underlying API call.
    :type api_params: Any

    Usage:
    The decorated function can return either a single prompt or a list of ell.Message objects:

    .. code-block:: python

       @ell.simple(model="gpt-4", temperature=0.7)
       def summarize_text(text: str) -> str:
           '''You are an expert at summarizing text.''' # System prompt
           return f"Please summarize the following text:\\n\\n{text}" # User prompt


       @ell.simple(model="gpt-4", temperature=0.7)
       def describe_image(image : PIL.Image.Image) -> List[ell.Message]:
           '''Describe the contents of an image.''' # unused because we're returning a list of Messages
           return [
               # helper function for ell.Message(text="...", role="system")
               ell.system("You are an AI trained to describe images."),
               # helper function for ell.Message(content="...", role="user")
               ell.user(["Describe this image in detail.", image]),
           ]


       image_description = describe_image(PIL.Image.open("https://example.com/image.jpg"))
       print(image_description) 
       # Output will be a string text-only description of the image

       summary = summarize_text("Long text to summarize...")
       print(summary)
       # Output will be a text-only summary

    Notes:

    - This decorator is designed for text-only model outputs, but supports multimodal inputs.
    - It simplifies complex responses from language models to text-only format, regardless of 
      the model's capability for structured outputs, function calling, or multimodal outputs.
    - For preserving complex model outputs (e.g., structured data, function calls, or multimodal 
      outputs), use the @ell.complex decorator instead. @ell.complex returns a Message object (role='assistant')
    - The decorated function can return a string or a list of ell.Message objects for more 
      complex prompts, including multimodal inputs.
    - If called with n > 1 in api_params, the wrapped LMP will return a list of strings for the n parallel outputs
      of the model instead of just one string. Otherwise, it will return a single string.
    - You can pass LM API parameters either in the decorator or when calling the decorated function.
      Parameters passed during the function call will override those set in the decorator.

    Example of passing LM API params:

    .. code-block:: python

       @ell.simple(model="gpt-4", temperature=0.7)
       def generate_story(prompt: str) -> str:
           return f"Write a short story based on this prompt: {prompt}"

       # Using default parameters
       story1 = generate_story("A day in the life of a time traveler")

       # Overriding parameters during function call
       story2 = generate_story("An AI's first day of consciousness", lm_params={"temperature": 0.9, "max_tokens": 500})

    See Also:

    - :func:`ell.complex`: For LMPs that preserve full structure of model responses, including multimodal outputs.
    - :func:`ell.tool`: For defining tools that can be used within complex LMPs.
    - :mod:`ell.studio`: For visualizing and analyzing LMP executions.
    """
    assert 'tools' not in api_params, "tools are not supported in lm decorator, use multimodal decorator instead"
    assert 'tool_choice' not in api_params, "tool_choice is not supported in lm decorator, use multimodal decorator instead"
    assert 'response_format' not in api_params, "response_format is not supported in lm decorator, use multimodal decorator instead"

    def convert_multimodal_response_to_lstr(response):
        return [x.content[0].text for x in response] if isinstance(response, list) else response.content[0].text
    return complex(model, client,  exempt_from_tracking, **api_params, post_callback=convert_multimodal_response_to_lstr)


