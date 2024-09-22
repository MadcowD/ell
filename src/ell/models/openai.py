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
    #XXX: Deprecation in 0.1.0
    standard_models = [
        'gpt-4-1106-preview',
        'gpt-4-32k-0314',
        'text-embedding-3-large',
        'gpt-4-0125-preview',
        'babbage-002',
        'gpt-4-turbo-preview',
        'gpt-4o',
        'gpt-4o-2024-05-13',
        'gpt-4o-mini-2024-07-18',
        'gpt-4o-mini',
        'gpt-4o-2024-08-06',
        'gpt-3.5-turbo-0301',
        'gpt-3.5-turbo-0613',
        'tts-1',
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-16k',
        'davinci-002',
        'gpt-3.5-turbo-16k-0613',
        'gpt-4-turbo-2024-04-09',
        'gpt-3.5-turbo-0125',
        'gpt-4-turbo',
        'gpt-3.5-turbo-1106',
        'gpt-3.5-turbo-instruct-0914',
        'gpt-3.5-turbo-instruct',
        'gpt-4-0613',
        'gpt-4',
        'gpt-4-0314',
    ]
    for model_id in standard_models:
        config.register_model(model_id, client)

    #XXX: Deprecation in 0.1.0
    config.register_model('o1-preview', client, supports_streaming=False)
    config.register_model('o1-mini', client, supports_streaming=False)

default_client = None
try:
    default_client = openai.Client()
except openai.OpenAIError as e:
    pass

register(default_client)
config.default_client = default_client