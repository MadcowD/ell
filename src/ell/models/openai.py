"""
This module handles the registration of OpenAI models within the ell framework.

It provides functionality to register various OpenAI models with a given OpenAI client,
making them available for use throughout the system. The module also sets up a default
client behavior for unregistered models.

Key features:
1. Registration of specific OpenAI models with their respective types (system, openai, openai-internal).
2. Utilization of a default OpenAI client for any unregistered models,

The default client behavior ensures that even if a specific model is not explicitly
registered, the system can still attempt to use it with the default OpenAI client.
This fallback mechanism provides flexibility in model usage while maintaining a
structured approach to model registration.

Note: The actual model availability may depend on your OpenAI account's access and the
current offerings from OpenAI.

Additionally, due to the registration of default mdoels, the OpenAI client may be used for
anthropic, cohere, groq, etc. models if their clients are not registered or fail
to register due to an error (lack of API keys, rate limits, etc.)
"""

from ell.configurator import config
import openai

import logging
import colorama

logger = logging.getLogger(__name__)

def register(client: openai.Client):
    """
    Register OpenAI models with the provided client.

    This function takes an OpenAI client and registers various OpenAI models
    with the global configuration. It allows the system to use these models
    for different AI tasks.

    Args:
        client (openai.Client): An instance of the OpenAI client to be used
                                for model registration.

    Note:
        The function doesn't return anything but updates the global
        configuration with the registered models.
    """
    model_data = [
        ('gpt-4-1106-preview', 'system'),
        ('gpt-4-32k-0314', 'openai'),
        ('text-embedding-3-large', 'system'),
        ('gpt-4-0125-preview', 'system'),
        ('babbage-002', 'system'),
        ('gpt-4-turbo-preview', 'system'),
        ('gpt-4o', 'system'),   
        ('gpt-4o-2024-05-13', 'system'),
        ('gpt-4o-mini-2024-07-18', 'system'),
        ('gpt-4o-mini', 'system'),
        ('gpt-4o-2024-08-06', 'system'),
        ('gpt-3.5-turbo-0301', 'openai'),
        ('gpt-3.5-turbo-0613', 'openai'),
        ('tts-1', 'openai-internal'),
        ('gpt-3.5-turbo', 'openai'),
        ('gpt-3.5-turbo-16k', 'openai-internal'),   
        ('davinci-002', 'system'),
        ('gpt-3.5-turbo-16k-0613', 'openai'),
        ('gpt-4-turbo-2024-04-09', 'system'),
        ('gpt-3.5-turbo-0125', 'system'),
        ('gpt-4-turbo', 'system'),
        ('gpt-3.5-turbo-1106', 'system'),
        ('gpt-3.5-turbo-instruct-0914', 'system'),
        ('gpt-3.5-turbo-instruct', 'system'),
        ('gpt-4-0613', 'openai'),
        ('gpt-4', 'openai'),
        ('gpt-4-0314', 'openai')
    ]
    for model_id, owned_by in model_data:
        config.register_model(model_id, client)

default_client = None
try:
    default_client = openai.Client()
except openai.OpenAIError as e:
    pass

register(default_client)
config.default_client = default_client