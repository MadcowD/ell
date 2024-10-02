============
@ell.complex
============

While ``@ell.simple`` provides a straightforward way to work with language models that return text, modern language models are increasingly capable of handling and generating multimodal content, structured outputs, and complex interactions. This is where ``@ell.complex`` comes into play.

The ``@ell.complex`` decorator is designed to handle sophisticated interactions with language models, including multimodal inputs/outputs, structured data, and tool usage. It extends ``@ell.simple``'s capabilities to address the evolving nature of language models, which can now process images, generate structured data, make function calls, and engage in multi-turn conversations. By returning rich ``Message`` objects instead of simple strings, ``@ell.complex`` enables more nuanced and powerful interactions, overcoming the limitations of traditional string-based interfaces in these advanced scenarios.


.. note:: Messages in ell are not the same as the dictionary messages used in the OpenAI API. ell's Message API provides a more intuitive and flexible way to construct and manipulate messages. You can read more about ell's Message API and type coercion in the :doc:`message_api` page.


Usage
-----

The basic usage of ``@ell.complex`` is similar to ``@ell.simple``, but with enhanced capabilities:

.. code-block:: python

    import ell
    from pydantic import BaseModel, Field

    class MovieReview(BaseModel):
        title: str = Field(description="The title of the movie")
        rating: int = Field(description="The rating of the movie out of 10")
        summary: str = Field(description="A brief summary of the movie")

    @ell.complex(model="gpt-4o-2024-08-06", response_format=MovieReview)
    def generate_movie_review(movie: str):
        """You are a movie review generator. Given the name of a movie, you need to return a structured review."""
        return f"Generate a review for the movie {movie}"

    review_message = generate_movie_review("The Matrix")
    review = review_message.parsed
    print(f"Movie: {review.title}, Rating: {review.rating}/10")
    print(f"Summary: {review.summary}")

Key Features
------------

1. Structured Outputs
^^^^^^^^^^^^^^^^^^^^^

``@ell.complex`` allows for structured outputs using Pydantic models:

.. code-block:: python

    @ell.complex(model="gpt-4o-2024-08-06", response_format=MovieReview)
    def generate_movie_review(movie: str) -> MovieReview:
        """You are a movie review generator. Given the name of a movie, you need to return a structured review."""
        return f"Generate a review for the movie {movie}"

    review_message = generate_movie_review("Inception")
    review = review_message.parsed
    print(f"Rating: {review.rating}/10")

2. Multimodal Interactions
^^^^^^^^^^^^^^^^^^^^^^^^^^

``@ell.complex`` can handle various types of inputs and **outputs**, including text and images:

.. code-block:: python

    from PIL import Image

    @ell.complex(model="gpt-5-omni")
    def describe_and_generate(prompt: str):
        return [
            ell.system("You can describe images and generate new ones based on text prompts."),
            ell.user(prompt)
        ]

    result = describe_and_generate("A serene lake at sunset")
    print(result.text)  # Prints the description
    if result.images:
        result.images[0].show()  # Displays the generated image

3. Chat-based Use Cases
^^^^^^^^^^^^^^^^^^^^^^^

``@ell.complex`` is particularly useful for chat-based applications where you need to maintain conversation history:

.. code-block:: python

    from ell import Message

    @ell.complex(model="gpt-4o", temperature=0.7)
    def chat_bot(message_history: List[Message]) -> List[Message]:
        return [
            ell.system("You are a friendly chatbot. Engage in casual conversation."),
        ] + message_history

    message_history = []
    while True:
        user_input = input("You: ")
        message_history.append(ell.user(user_input))
        response = chat_bot(message_history)
        print("Bot:", response.text)
        message_history.append(response)

4. Tool Usage
^^^^^^^^^^^^^

``@ell.complex`` supports tool usage, allowing language models to make function calls:

.. code-block:: python

    @ell.tool()
    def get_weather(location: str = Field(description="The full name of a city and country, e.g. San Francisco, CA, USA")):
        """Get the current weather for a given location."""
        # Simulated weather API call
        return f"The weather in {location} is sunny."

    @ell.complex(model="gpt-4-turbo", tools=[get_weather])
    def travel_planner(destination: str):
        """Plan a trip based on the destination and current weather."""
        return [
            ell.system("You are a travel planner. Use the weather tool to provide relevant advice."),
            ell.user(f"Plan a trip to {destination}")
        ]

    result = travel_planner("Paris")
    print(result.text)  # Prints travel advice
    if result.tool_calls:
        # This is done so that we can pass the tool calls to the language model
        result_message = result.call_tools_and_collect_as_message()
        print("Weather info:", result_message.tool_results[0].text) # Raw text of the tool call.
        print("Message to be sent to the LLM:", result_message.text) # Representation of the message to be sent to the LLM.


Reference
---------

.. autofunction:: ell.complex
