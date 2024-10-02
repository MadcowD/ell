from typing import Any
from ell.configurator import config
import logging

logger = logging.getLogger(__name__)


def register(client: Any):
    """
    Register Bedrock models with the provided client.

    This function takes an boto3 client and registers various Bedrock models
    with the global configuration. It allows the system to use these models
    for different AI tasks.

    Args:
        client (boto3.client): An instance of the bedrock client to be used
                                        for model registration.

    Note:
        The function doesn't return anything but updates the global
        configuration with the registered models.
    """
    model_data = [
        ('anthropic.claude-3-opus-20240229-v1:0', 'bedrock'),
        ('anthropic.claude-3-sonnet-20240229-v1:0', 'bedrock'),
        ('anthropic.claude-3-haiku-20240307-v1:0', 'bedrock'),
        ('anthropic.claude-3-5-sonnet-20240620-v1:0', 'bedrock'),

        ('mistral.mistral-7b-instruct-v0:2', 'bedrock'),
        ('mistral.mixtral-8x7b-instruct-v0:1', 'bedrock'),
        ('mistral.mistral-large-2402-v1:0', 'bedrock'),
        ('mistral.mistral-small-2402-v1:0', 'bedrock'),


        ('ai21.jamba-instruct-v1:0','bedrock'),
        ('ai21.j2-ultra-v1', 'bedrock'),
        ('ai21.j2-mid-v1', 'bedrock'),

        ('amazon.titan-embed-text-v1', 'bedrock'),
        ('amazon.titan-text-lite-v1', 'bedrock'),
        ('amazon.titan-text-express-v1', 'bedrock'),
        ('amazon.titan-image-generator-v2:0', 'bedrock'),
        ('amazon.titan-image-generator-v1', 'bedrock'),

        ('cohere.command-r-plus-v1:0', 'bedrock'),
        ('cohere.command-r-v1:0', 'bedrock'),
        ('cohere.embed-english-v3', 'bedrock'),
        ('cohere.embed-multilingual-v3', 'bedrock'),
        ('cohere.command-text-v14', 'bedrock'),

        ('meta.llama3-8b-instruct-v1:0', 'bedrock'),
        ('meta.llama3-70b-instruct-v1:0', 'bedrock'),
        ('meta.llama2-13b-chat-v1', 'bedrock'),
        ('meta.llama2-70b-chat-v1', 'bedrock'),
        ('meta.llama2-13b-v1', 'bedrock'),

    ]

    for model_id, owned_by in model_data:
        config.register_model(name=model_id, default_client=client, supports_streaming=True)

default_client = None
try:

    import boto3
    default_client = boto3.client('bedrock-runtime')
except Exception as e:
    pass

register(default_client)
