import logging
from ell.configurator import config
from ell.providers import openrouter

logger = logging.getLogger(__name__)

client = None  # Global: OpenRouter client


def register_openrouter_models(openrouter_client: openrouter.Client):
    try:
        models = openrouter_client.get_models()
        for model_id in models:
            config.register_model(model_id, client)
        logger.info(f"Registered {len(models)} OpenRouter models successfully.")
    except Exception as e:
        logger.error(f"Failed to fetch and register OpenRouter models: {e}")

try:
    client = openrouter.get_client()
    register_openrouter_models(client)
    logger.info("Default OpenRouter client created and models registered successfully.")
except Exception as e:
    logger.warning(f"Failed to create default OpenRouter client or register models: {e}")
