===========
@ell.simple
===========


The core unit of prompt engineering in ell is the ``@ell.simple`` decorator. This decorator transforms a function that provides system and user prompts into a callable object. When invoked, this callable sends the provided prompts to a language model and returns the model's response. 

The development of ``@ell.simple`` is driven by several important objectives:

- Improve readability and usabiltiy of prompt engineering code.
- Force a functional decomposition of prompt systems into reusable components.
- Enable versioning, serialization, and tracking of prompts over time


Usage
-----

The ``@ell.simple`` decorator can be used in two main ways:

1. Using the docstring as the system prompt, and the return value as the user message:

   .. code-block:: python

      @ell.simple(model="gpt-4")
      def hello(name: str):
          """You are a helpful assistant."""
          return f"Say hello to {name}!"

2. Explicitly defining messages:

   .. code-block:: python

      @ell.simple(model="gpt-4")
      def hello(name: str):
          return [
              ell.system("You are a helpful assistant."),
              ell.user(f"Say hello to {name}!")
          ]

.. note:: Messages in ell are not the same as the dictionary messages used in the OpenAI API. ell's Message API provides a more intuitive and flexible way to construct and manipulate messages. You can read more about ell's Message API and type coercion in the :doc:`message_api` page.


Invoking an ``ell.simple`` LMP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To use the decorated function, we can call it as a normal function. However, instead of receiving the typical return value, we will receive the result of passing the system and user prompts directly to the model specified in the decorator constructor, in this case GPT-4.

.. code-block:: python

    >>> hello("world")
    'Hello, world!'

As you can see from this example, the return type of an ``ell.simple`` LMP is a string. This is to optimize for readability and usability, as most invocations of language models revolve around passing strings around. Additional metadata is only needed occasionally.

Therefore, we have two decorators within the ell framework:

1. ``@ell.simple``: Returns simple strings, as shown here.

2. ``@ell.complex``: Returns message objects containing all of the typical message API metadata and additional helper functions for interacting with multimodal output data. You can read more about this in the :doc:`ell_complex` page.


Variable system prompts
^^^^^^^^^^^^^^^^^^^^^^^

One of the challenges with specifying the system prompt in the docstring of a language model program is that if you want to use variable system prompts, Python will no longer treat the string literal at the top of the function as a docstring. For example:

.. code-block:: python

    def my_func(var : int):
        f"""my variable doc string for my_func. {var}"""
        pass

.. code-block:: python

    >>> my_func.__doc__
    None

This behavior makes sense because a function's docstring should not change during execution and should be extractable through static analysis.

To address this issue with ``@ell.simple``, you need to use the second method of defining an ``ell.simple`` language model program by creating a function that returns a list of messages (see :doc:`message_api` for more details).

.. code-block:: python

    @ell.simple(model="gpt-4")
    def my_func(name : str, var : int):
        return [
            ell.system(f"You are a helpful assistant. {var}"),
            ell.user(f"Say hello to {name}!")
        ]

With this approach, ell will ignore the docstring of ``my_func`` and instead supply the messages returned by the function to the language model API.

Passing parameters to an LLM API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
One of the most convenient functions of the ``@ell.simple`` decorator is that you can easily pass parameters to an LLM API, both at definition time and runtime. For example, models within the OpenAI API have parameters like ``temperature``, ``max_tokens``, stop tokens, and ``logit_bias``. Due to how ``@ell.simple`` works, you can simply specify these in the decorator as keyword arguments.

.. code-block:: python

    @ell.simple(model="gpt-4", temperature=0.5, max_tokens=100, stop=["."])
    def hello(name: str):
        """You are a helpful assistant."""
        return f"Hey there {name}!"
        
Likewise, if you want to modify those parameters for a particular invocation of that prompt, you simply pass them in as ``api_params`` keyword arguments to the function when calling it. For example:

.. code-block:: python

    >>> hello("world", api_params=dict(temperature=0.7))
    'Hey there world!'


Multiple outputs (n>1)
~~~~~~~~~~~~~~~~~~~~~~~
As is often important in prompt engineering to leverage test-time compute, many language model APIs allow you to specify a count parameter, usually 'n', which will generate several outputs from the language model given a particular prompt.

In the OpenAI API, for example, this is actually quite cumbersome because the API specification separates different completions into 'choices' objects. For example:

.. code-block:: python

    response = openai.Completion.create(
        model="gpt-4",
        prompt="Say hello to everyone",
        n=2
    )
    
    r1 = response.choices[0].text
    r2 = response.choices[1].text

In the spirit of simplicity, we've designed it to automatically coerce the return type into the correct shape, similar to NumPy and PyTorch. This means that when you call an ``ell.simple`` language model program with ``n`` greater than one, instead of returning a string, it returns a list of strings.

.. code-block:: python

    @ell.simple(model="gpt-4", n=2)
    def hello(name: str):
        """You are a helpful assistant."""
        return f"Say hello to {name}!"

.. code-block:: python

    >>> hello("world")
    ['Hey there world!', 'Hi, world.']

Similarly, this behavior applies when using runtime ``api_params`` to specify multiple outputs.

.. code-block:: python

    >>> hello("world", api_params=dict(n=3))
    ['Hey there world!', 'Hi, world.', 'Hello, world!']


.. note:: In the future, we may modify this interface as preserving the ``api_params`` keyword in its current form could potentially lead to conflicts with user-defined functions. However, during the beta phase, we are closely monitoring for feedback and will make adjustments based on user experiences and needs.


Multimodal inputs
^^^^^^^^^^^^^^^^^
``@ell.simple`` supports multimodal inputs, allowing you to easily work with both text and images in your language model programs. This is particularly useful for models with vision capabilities, such as GPT-4 with vision.

Here's an example of how to use ``@ell.simple`` with multimodal inputs:

.. code-block:: python

    from PIL import Image
    import ell
    from ell.types.message import ImageContent

    @ell.simple(model="gpt-4-vision-preview")
    def describe_image(image: Image.Image):
        return [
            ell.system("You are a helpful assistant that describes images."),
            ell.user(["What's in this image?", image])
            # Or ell.user(["What's in this image?", ImageContent(url=image_url, detail="low")])
        ]

    # Usage with PIL Image
    image = Image.open("path/to/your/image.jpg")
    description = describe_image(image)
    print(description)  # This will print a text description of the image


In these examples, the ``describe_image`` function takes a PIL Image object as input, while ``describe_image_url`` takes a string URL. The ``ell.user`` message combines both text and image inputs. ``@ell.simple`` automatically handles the conversion of the PIL Image object or ImageContent into the appropriate format for the language model.

This approach simplifies working with multimodal inputs, allowing you to focus on your application logic rather than the intricacies of API payloads.

.. note:: Not all language model providers support image URLs. For example, as of the current version, Anthropic's models do not support image URLs. Always check the capabilities and requirements of your chosen language model provider when working with multimodal inputs.

.. warning:: While ``@ell.simple`` supports multimodal inputs, it is designed to return text-only outputs. For handling multimodal outputs (such as generated images or audio), you need to use ``@ell.complex``. Please refer to the :doc:`ell_complex` documentation for more information on working with multimodal outputs.



What about multiturn conversations, tools, structured outputs, and other features?
----------------------------------------------------------------------------------

While ``@ell.simple`` is great for straightforward text-based interactions with language models, there are scenarios where you might need more complex functionality. For instance, you may want to work with multiturn conversations, utilize tools, generate structured outputs, or handle multimodal content beyond just text.

In such cases, you'll need an LMP that can return rich ``Message`` objects instead of just strings. This is where ``@ell.complex`` comes into play. The ``@ell.complex`` decorator provides enhanced capabilities for more sophisticated interactions with language models.

For more information on how to use ``@ell.complex`` and its advanced features, please refer to the :doc:`ell_complex` documentation.


Reference
---------

.. autofunction:: ell.simple
