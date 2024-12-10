"""
This module handles the registration of Google Gemini models within the ell framework.

It provides functionality to register various Google Gemini models with a given Google Gemini client,
making them available for use throughout the system. The module also sets up a default
client behavior for unregistered models.

Key features:
1. Registration of specific Google models with their respective types (system, google, google-internal).
2. Utilization of a default Google client for any unregistered models,

The default client behavior ensures that even if a specific model is not explicitly
registered, the system can still attempt to use it with the default Google client.
This fallback mechanism provides flexibility in model usage while maintaining a
structured approach to model registration.

Note: The actual model availability may depend on your Google account's access and the
current offerings from Google.

In this file, we use google's openai compatible client to perform the registration.
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
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b',
    'gemini-1.5-pro',
    'gemini-1.0-pro',
    'aqa',
    ]
    for model_id in standard_models:
        config.register_model(model_id, client)


default_client = None
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise openai.OpenAIError("GEMINI_API_KEY not found in environment variables")
    default_client = openai.Client(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=gemini_api_key)
except openai.OpenAIError as e:
    pass

register(default_client)
config.default_client = default_client