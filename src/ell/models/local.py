import logging

from ell.configurator import config
from ell.providers.local import LocalModelClient

logger = logging.getLogger(__name__)
client = None


def register(model_name: str, model_path: str):
    """
    Registers model from local disk

    This function sets up the Ollama client with the given base URL and
    fetches available models from the Ollama API. It then registers these
    models with the global configuration, allowing them to be used within
    the ell framework.

    Args:
        model_name (str): The name of the model to register.
        model_path (str): The path to the model on disk.

    Note:
        This function updates the global client and configuration.
        It logs any errors encountered during the process.
    """

    client = LocalModelClient(model_name=model_name, model_path=model_path)
    config.register_model(model_name, client)
