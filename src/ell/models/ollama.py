from ell.configurator import config
import openai
import requests
import logging

logger = logging.getLogger(__name__)
client = None

def register(base_url):
    global client
    client = openai.Client(base_url=base_url)
    
    try:
        response = requests.get(f"{base_url}/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        
        for model in models:
            config.register_model(model["name"], client)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch models from {base_url}: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

