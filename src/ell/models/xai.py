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

import os
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
    standard_models = [
    'grok-2-mini',
    'grok-2',
    'grok-2-mini-public',
    'grok-2-public',
    ]
    for model_id in standard_models:
        config.register_model(model_id, client)


default_client = None
try:

    xai_api_key = os.environ.get("XAI_API_KEY")
    if not xai_api_key:
        raise openai.OpenAIError("XAI_API_KEY not found in environment variables")
    default_client = openai.Client(base_url="https://api.x.ai/v1", api_key=xai_api_key)
except openai.OpenAIError as e:
    pass

register(default_client)
config.default_client = default_client