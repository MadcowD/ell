Language Model Programs (LMPs)
==============================

Introduction
------------

Language Model Programs (LMPs) are a core concept in ell. They represent a paradigm shift in how we interact with large language models, treating prompts not as simple strings, but as full-fledged programs with logic, structure, and reusability.

What are Language Model Programs?
---------------------------------

An LMP in ell is a Python function decorated with either ``@ell.simple`` or ``@ell.complex``. This function encapsulates the logic for generating a prompt or a series of messages to be sent to a language model.

Key characteristics of LMPs:

1. **Encapsulation**: All the logic for creating a prompt is contained within a single function.
2. **Reusability**: LMPs can be easily reused across different parts of your application.
3. **Versioning**: ell automatically versions your LMPs, allowing you to track changes over time.
4. **Tracing**: Every invocation of an LMP is traced, providing insights into your application's behavior.

Simple vs Complex LMPs
----------------------

ell provides two main types of LMPs:

Simple LMPs
^^^^^^^^^^^

Simple LMPs are created using the ``@ell.simple`` decorator. They are designed for straightforward, single-turn interactions with a language model.

Example of a Simple LMP:

.. code-block:: python

    @ell.simple(model="gpt-4")
    def summarize_text(text: str) -> str:
        """You are an expert at summarizing text."""
        return f"Please summarize the following text:\n\n{text}"

Key points:

- The function's docstring becomes the system prompt.
- The return value becomes the user prompt.
- The LMP returns a single string response from the model.

Complex LMPs
^^^^^^^^^^^^

Complex LMPs are created using the ``@ell.complex`` decorator. They allow for more advanced scenarios, including:

- Multi-turn conversations
- Tool usage
- Structured inputs and outputs
- Multimodal interactions

Example of a Complex LMP:

.. code-block:: python

    @ell.complex(model="gpt-4", tools=[some_tool])
    def interactive_assistant(message_history: List[ell.Message]) -> List[ell.Message]:
        return [
            ell.system("You are a helpful assistant with access to tools."),
        ] + message_history

Key points:

- Complex LMPs work with lists of ``ell.Message`` objects.
- They can integrate tools and handle multi-turn conversations.
- They offer more control over the interaction with the language model.

Benefits of Language Model Programs
-----------------------------------

1. **Modularity**: LMPs encourage breaking down complex prompt engineering tasks into manageable, reusable components.
2. **Versioning**: Automatic versioning allows you to track changes and compare different iterations of your prompts.
3. **Tracing**: Invocation tracing helps in debugging and optimizing your language model interactions.
4. **Type Safety**: By using Python's type hints, LMPs provide better code clarity and catch potential errors early.
5. **Testability**: LMPs can be easily unit tested, improving the reliability of your prompt engineering process.

Best Practices for LMPs
-----------------------

1. Keep each LMP focused on a single task or concept.
2. Use descriptive names for your LMP functions.
3. Leverage the function's docstring to provide clear instructions to the language model.
4. Use type hints to clarify the expected inputs and outputs of your LMPs.
5. For complex interactions, break down your logic into multiple LMPs that can be composed together.

Conclusion
----------

Language Model Programs are a powerful abstraction that allows you to work with language models in a more structured, maintainable, and scalable way. By thinking of prompts as programs, ell enables you to apply software engineering best practices to the field of prompt engineering.