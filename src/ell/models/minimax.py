"""
This module handles the registration of MiniMax models within the ell framework.

MiniMax provides OpenAI-compatible API endpoints, so models are registered
using the OpenAI client with the MiniMax base URL.

Key features:
1. Registration of MiniMax models (MiniMax-M2.7, MiniMax-M2.7-highspeed, MiniMax-M2.5, MiniMax-M2.5-highspeed).
2. Automatic client setup using the MINIMAX_API_KEY environment variable.

MiniMax API docs: https://www.minimaxi.com/document/introduction

Note: MiniMax models support OpenAI-compatible chat completions, streaming,
and tool/function calling.
"""

import os
from ell.configurator import config
import openai

import logging

logger = logging.getLogger(__name__)

MINIMAX_MODELS = [
    "MiniMax-M2.7",
    "MiniMax-M2.7-highspeed",
    "MiniMax-M2.5",
    "MiniMax-M2.5-highspeed",
]


def register(client: openai.Client = None, api_key: str = None):
    """
    Register MiniMax models with the provided client.

    Args:
        client (openai.Client, optional): An OpenAI-compatible client configured
            for MiniMax. If not provided, one will be created using the
            MINIMAX_API_KEY environment variable.
        api_key (str, optional): MiniMax API key. If not provided, the
            MINIMAX_API_KEY environment variable is used.
    """
    if client is None:
        key = api_key or os.environ.get("MINIMAX_API_KEY")
        if not key:
            raise openai.OpenAIError(
                "MINIMAX_API_KEY not found. Set the MINIMAX_API_KEY environment "
                "variable or pass api_key to register()."
            )
        client = openai.Client(
            base_url="https://api.minimax.io/v1",
            api_key=key,
        )
    for model_id in MINIMAX_MODELS:
        config.register_model(model_id, client)


default_client = None
try:
    minimax_api_key = os.environ.get("MINIMAX_API_KEY")
    if not minimax_api_key:
        raise openai.OpenAIError(
            "MINIMAX_API_KEY not found in environment variables"
        )
    default_client = openai.Client(
        base_url="https://api.minimax.io/v1",
        api_key=minimax_api_key,
    )
except openai.OpenAIError:
    pass

if default_client is not None:
    for model_id in MINIMAX_MODELS:
        config.register_model(model_id, default_client)
