Decorators in ell
=================

Introduction
------------

Decorators are a fundamental concept in ell, used to transform regular Python functions into Language Model Programs (LMPs). ell provides two main decorators: ``@ell.simple`` and ``@ell.complex``. Understanding these decorators is crucial for effectively using ell in your projects.

@ell.simple Decorator
---------------------

The ``@ell.simple`` decorator is used for straightforward, text-in-text-out interactions with language models.

Syntax
^^^^^^

.. code-block:: python

    @ell.simple(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, **api_params)
    def my_simple_lmp(input_param: str) -> str:
        """System prompt goes here."""
        return f"User prompt based on {input_param}"

Parameters
^^^^^^^^^^

- ``model``: The name or identifier of the language model to use (e.g., "gpt-4").
- ``client``: An optional OpenAI client instance. If not provided, a default client will be used.
- ``exempt_from_tracking``: If True, the LMP usage won't be tracked. Default is False.
- ``**api_params``: Additional keyword arguments to pass to the underlying API call (e.g., temperature, max_tokens).

Usage
^^^^^

.. code-block:: python

    @ell.simple(model="gpt-4", temperature=0.7)
    def generate_haiku(topic: str) -> str:
        """You are a master haiku poet. Create a haiku about the given topic."""
        return f"Write a haiku about: {topic}"

    haiku = generate_haiku("autumn leaves")
    print(haiku)

Key Points
^^^^^^^^^^

1. The function's docstring becomes the system prompt.
2. The return value of the function becomes the user prompt.
3. The decorated function returns a string, which is the model's response.
4. Supports multimodal inputs but always returns text.

@ell.complex Decorator
----------------------

The ``@ell.complex`` decorator is used for more advanced scenarios, including multi-turn conversations, tool usage, and structured outputs.

Syntax
^^^^^^

.. code-block:: python

    @ell.complex(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, tools: Optional[List[Callable]] = None, **api_params)
    def my_complex_lmp(message_history: List[ell.Message]) -> List[ell.Message]:
        return [
            ell.system("System message here"),
            *message_history
        ]

Parameters
^^^^^^^^^^

- ``model``: The name or identifier of the language model to use.
- ``client``: An optional OpenAI client instance.
- ``exempt_from_tracking``: If True, the LMP usage won't be tracked.
- ``tools``: A list of tool functions that can be used by the LLM.
- ``**api_params``: Additional API parameters.

Usage
^^^^^

.. code-block:: python

    @ell.complex(model="gpt-4", tools=[get_weather])
    def weather_assistant(message_history: List[ell.Message]) -> List[ell.Message]:
        return [
            ell.system("You are a weather assistant with access to real-time weather data."),
            *message_history
        ]

    response = weather_assistant([ell.user("What's the weather like in New York?")])
    print(response.text)

    if response.tool_calls:
        tool_results = response.call_tools_and_collect_as_message()
        final_response = weather_assistant(message_history + [response, tool_results])
        print(final_response.text)

Key Points
^^^^^^^^^^

1. Works with lists of ``ell.Message`` objects for more complex interactions.
2. Supports tool integration for expanded capabilities.
3. Can handle multi-turn conversations and maintain context.
4. Allows for structured inputs and outputs using Pydantic models.
5. Supports multimodal inputs and outputs.

Choosing Between Simple and Complex
-----------------------------------

- Use ``@ell.simple`` for:
    - Single-turn, text-in-text-out interactions
    - Quick prototyping and simple use cases
    - When you don't need tool integration or structured outputs

- Use ``@ell.complex`` for:
    - Multi-turn conversations
    - Integrating tools or external data sources
    - Working with structured data (using Pydantic models)
    - Multimodal inputs or outputs
    - Advanced control over the interaction flow

Best Practices
--------------

1. Start with ``@ell.simple`` for basic tasks and migrate to ``@ell.complex`` as your needs grow.
2. Use clear and concise docstrings to provide effective system prompts.
3. Leverage type hints for better code clarity and error catching.
4. When using ``@ell.complex``, break down complex logic into smaller, composable LMPs.
5. Use the ``exempt_from_tracking`` parameter judiciously, as tracking provides valuable insights.

By mastering these decorators, you'll be able to create powerful and flexible Language Model Programs tailored to your specific needs.