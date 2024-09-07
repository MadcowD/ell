Messages and Content Blocks in ell
==================================

In ell, the Message and ContentBlock classes are fundamental to handling communication with language models, especially in multi-turn conversations and when dealing with various types of content. This guide will help you understand how to work with these important components.

Messages
--------

A Message in ell represents a single interaction in a conversation with a language model. It has two main components:

1. A role (e.g., "system", "user", "assistant")
2. Content (represented by a list of ContentBlocks)

Creating Messages
^^^^^^^^^^^^^^^^^

ell provides helper functions to create messages with specific roles:

.. code-block:: python

    import ell

    system_message = ell.system("You are a helpful AI assistant.")
    user_message = ell.user("What's the weather like today?")
    assistant_message = ell.assistant("I'm sorry, I don't have access to real-time weather information.")

You can also create messages directly:

.. code-block:: python

    from ell import Message, ContentBlock

    message = Message(role="user", content=[ContentBlock(text="Hello, world!")])

Content Blocks
--------------

ContentBlocks are used to represent different types of content within a message. They can contain:

- Text
- Images
- Audio (future support)
- Tool calls
- Tool results
- Structured data (parsed content)

Creating Content Blocks
^^^^^^^^^^^^^^^^^^^^^^^

Here are examples of creating different types of ContentBlocks:

.. code-block:: python

    from ell import ContentBlock
    from PIL import Image

    # Text content block
    text_block = ContentBlock(text="This is a text message.")

    # Image content block
    image = Image.open("example.jpg")
    image_block = ContentBlock(image=image)

    # Tool call content block
    tool_call_block = ContentBlock(tool_call=some_tool_call)

    # Parsed content block (structured data)
    from pydantic import BaseModel

    class UserInfo(BaseModel):
        name: str
        age: int

    user_info = UserInfo(name="Alice", age=30)
    parsed_block = ContentBlock(parsed=user_info)

Working with Content Blocks in Messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can combine multiple ContentBlocks in a single Message:

.. code-block:: python

    multi_content_message = ell.user([
        ContentBlock(text="Here's an image of a cat:"),
        ContentBlock(image=cat_image)
    ])

Using Messages and Content Blocks in LMPs
-----------------------------------------

In complex LMPs, you'll often work with lists of Messages:

.. code-block:: python

    @ell.complex(model="gpt-4")
    def chat_bot(message_history: List[ell.Message]) -> List[ell.Message]:
        return [
            ell.system("You are a friendly chat bot."),
            *message_history,
            ell.assistant("How can I help you today?")
        ]

Accessing Message Content
-------------------------

You can access the content of a Message in different ways:

.. code-block:: python

    # Get all text content
    text_content = message.text

    # Get only the text content, excluding non-text elements
    text_only = message.text_only

    # Access specific content types
    tool_calls = message.tool_calls
    tool_results = message.tool_results
    structured = message.structured

Best Practices
--------------

1. Use the appropriate ContentBlock type for each piece of content.
2. When working with complex LMPs, always return a list of Messages.
3. Use the helper functions (ell.system, ell.user, ell.assistant) for clarity.
4. When dealing with multimodal content, combine different ContentBlock types in a single Message.

By mastering Messages and ContentBlocks, you'll be able to create sophisticated interactions with language models, handle various types of data, and build complex conversational flows in your ell applications.