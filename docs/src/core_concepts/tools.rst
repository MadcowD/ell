Tools in ell
============

Introduction
------------

Tools in ell are a powerful feature that allows Language Model Programs (LMPs) to interact with external functions or APIs. This enables LMPs to access real-world data, perform computations, or take actions based on the language model's decisions.

Defining Tools
--------------

Tools are defined using the ``@ell.tool()`` decorator. Here's the basic structure:

.. code-block:: python

    from pydantic import Field

    @ell.tool()
    def tool_name(param1: str, param2: int = Field(description="Parameter description")) -> str:
        """Tool description goes here."""
        # Tool implementation
        return "Result"

Key Points:

1. Use the ``@ell.tool()`` decorator to define a tool.
2. Provide type annotations for all parameters.
3. Use Pydantic's ``Field`` for additional parameter metadata.
4. Write a clear docstring describing the tool's purpose and usage.
5. The return type should be one of: ``str``, JSON-serializable object, Pydantic model, or ``List[ell.ContentBlock]``.

Example: Weather Tool
---------------------

Let's create a simple weather tool:

.. code-block:: python

    from pydantic import Field

    @ell.tool()
    def get_weather(
        location: str = Field(description="City name or coordinates"),
        unit: str = Field(description="Temperature unit: 'celsius' or 'fahrenheit'", default="celsius")
    ) -> str:
        """Get the current weather for a given location."""
        # Implement actual weather API call here
        return f"The weather in {location} is sunny and 25°{unit[0].upper()}"

Using Tools in LMPs
-------------------

To use tools in your LMPs, you need to:

1. Pass the tools to the ``@ell.complex`` decorator.
2. Handle tool calls in your LMP logic.

Here's an example:

.. code-block:: python

    @ell.complex(model="gpt-4", tools=[get_weather])
    def weather_assistant(message_history: List[ell.Message]) -> List[ell.Message]:
        return [
            ell.system("You are a helpful weather assistant. Use the get_weather tool when asked about weather."),
            *message_history
        ]

    # Using the weather assistant
    response = weather_assistant([ell.user("What's the weather like in Paris?")])

    if response.tool_calls:
        tool_results = response.call_tools_and_collect_as_message()
        final_response = weather_assistant(message_history + [response, tool_results])
        print(final_response.text)

Tool Results
------------

When a tool is called, it returns a ``ToolResult`` object, which contains:

- ``tool_call_id``: A unique identifier for the tool call.
- ``result``: A list of ``ContentBlock`` objects representing the tool's output.

You can access tool results using the ``tool_results`` property of the response message:

.. code-block:: python

    for tool_result in response.tool_results:
        print(f"Tool call ID: {tool_result.tool_call_id}")
        for content_block in tool_result.result:
            print(f"Result: {content_block.text}")

Parallel Tool Execution
-----------------------

For efficiency, ell supports parallel execution of multiple tool calls:

.. code-block:: python

    if response.tool_calls:
        tool_results = response.call_tools_and_collect_as_message(parallel=True, max_workers=3)

This can significantly speed up operations when multiple independent tool calls are made.

Best Practices for Tools
------------------------

1. **Atomic Functionality**: Design tools to perform single, well-defined tasks.
2. **Clear Documentation**: Provide detailed docstrings explaining the tool's purpose, parameters, and return value.
3. **Error Handling**: Implement robust error handling within your tools to gracefully manage unexpected inputs or API failures.
4. **Type Safety**: Use type annotations and Pydantic models to ensure type safety and clear interfaces.
5. **Stateless Design**: Where possible, design tools to be stateless to simplify usage and avoid unexpected behavior.
6. **Performance Considerations**: For tools that may be time-consuming, consider implementing caching or optimizing for repeated calls.

Limitations and Considerations
------------------------------

- Tools are only available in LMPs decorated with ``@ell.complex``.
- The language model decides when and how to use tools based on the conversation context and tool descriptions.
- Ensure that sensitive operations are properly secured, as tool usage is determined by the language model.

By effectively using tools, you can greatly extend the capabilities of your Language Model Programs, allowing them to interact with real-world data and systems in powerful ways.