========================
Models & API Clients
========================

In language model programming, the relationship between models and API clients is crucial. ell2a provides a robust framework for managing this relationship, offering various ways to specify clients for models, register custom models, and leverage default configurations.

Model Registration and Default Clients
--------------------------------------

ell2a automatically registers numerous models from providers like OpenAI, Anthropic, Cohere, and Groq upon initialization. This allows you to use models without explicitly specifying a client. 

If no client is found for a model, ell2a falls back to a default OpenAI client. This enables the utilization of newly released models without updating ell2a for new model registrations. If the fallback fails because the model is not available in the OpenAI API, you can register your own client for the model using the `ell2a.config.register_model` method or specify a client when calling the language model program below


Specifying Clients for Models
-----------------------------

ell2a offers multiple methods to specify clients for models:

1. Decorator-level Client Specification:

.. code-block:: python

    import ell2a
    import openai

    client = openai.Client(api_key="your-api-key")

    @ell2a.simple(model="gpt-next", client=client)
    def my_lmp(prompt: str):
        return f"Respond to: {prompt}"

2. Function Call-level Client Specification:

.. code-block:: python

    result = my_lmp("Hello, world!", client=another_client)

3. Global Client Registration:

.. code-block:: python

    ell2a.config.register_model("gpt-next", my_custom_client)

Custom Model Registration
-------------------------

For custom or newer models, ell2a provides a straightforward registration method:

.. code-block:: python

    import ell2a
    import my_custom_client

    ell2a.config.register_model("my-custom-model", my_custom_client)

