from ell.configurator import config
import openai

import logging

logger = logging.getLogger(__name__)

def register_openai_models(client : openai.Client):
    config.register_model("gpt-4o", client)
    config.register_model("gpt-3.5-turbo", client)
    config.register_model("gpt-4-turbo", client)



try:
    default_client = openai.Client()
    register_openai_models(default_client)
except Exception as e:
    logger.info(f"Error registering default OpenAI models: {e}. This is likely because you don't have an OpenAI key set. You need to reregister the models with a new client.")