from ell.configurator import config
import ollama
import requests
import logging

logger = logging.getLogger(__name__)
client = None

def register(base_url):
    global client
    client = ollama.Client(host=base_url)
    
    try:
        models = client.list()
        
        if 'models' in models:
            for model in models['models']:
                config.register_model(model['name'], client)
            logger.info(f"Registered {len(models['models'])} Ollama models")
        else:
            logger.warning("No models found in Ollama response")
    except Exception as e:
        logger.error(f"An error occurred while registering Ollama models: {e}")