# src/ell/models/openrouter.py
import logging
from typing import Dict, List

from ell.configurator import config
from ell.providers import openrouter

logger = logging.getLogger(__name__)

client = None  # Global: OpenRouter client


class OpenRouterModel:
    def __init__(self, model_data: Dict):
        self.id = model_data["id"]
        self.name = model_data["name"]
        self.created = model_data["created"]
        self.description = model_data["description"]
        self.context_length = model_data["context_length"]
        self.architecture = model_data["architecture"]
        self.pricing = model_data["pricing"]
        self.top_provider = model_data["top_provider"]
        self.per_request_limits = model_data["per_request_limits"]

    def __str__(self):
        return f"OpenRouterModel(id={self.id}, name={self.name})"


def fetch_openrouter_models(openrouter_client: openrouter.Client) -> List[OpenRouterModel]:
    return [OpenRouterModel(model_data) for model_data in openrouter_client.models.values()]


def register_openrouter_models(openrouter_client: openrouter.Client):
    try:
        models = fetch_openrouter_models(openrouter_client)
        for model in models:
            config.register_model(model.id, client)
        logger.info(f"Registered {len(models)} OpenRouter models successfully.")
    except Exception as e:
        logger.error(f"Failed to fetch and register OpenRouter models: {e}")

try:
    client = openrouter.get_client()
    register_openrouter_models(client)
    logger.info("Default OpenRouter client created and models registered successfully.")
except Exception as e:
    logger.warning(f"Failed to create default OpenRouter client or register models: {e}")
