# src/ell/models/groq.py
from ell.configurator import config
import logging
import os

logger = logging.getLogger(__name__)

try:
    from groq import Groq

    _groq_client = None  # Global variable to store the Groq client

    def register(client: Groq):
        model_data = [
            ('distil-whisper-large-v3-en', 'groq'),
            ('gemma2-9b-it', 'groq'),
            ('gemma-7b-it', 'groq'),
            ('llama3-groq-70b-8192-tool-use-preview', 'groq'),
            ('llama3-groq-8b-8192-tool-use-preview', 'groq'),
            ('llama-3.1-70b-versatile', 'groq'),
            ('llama-3.1-8b-instant', 'groq'),
            ('llama-guard-3-8b', 'groq'),
            ('llava-v1.5-7b-4096-preview', 'groq'),
            ('llama3-70b-8192', 'groq'),
            ('llama3-8b-8192', 'groq'),
            ('mixtral-8x7b-32768', 'groq'),
            ('whisper-large-v3', 'groq'),
        ]
        for model_id, owned_by in model_data:
            config.register_model(model_id, client)

    def get_groq_client() -> Groq:
        global _groq_client
        if _groq_client is not None:
            return _groq_client

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")

        _groq_client = Groq(api_key=api_key)
        register(_groq_client)
        return _groq_client

    try:
        default_client = get_groq_client()
        logger.info("Default Groq client created and models registered successfully.")
    except Exception as e:
        logger.warning(f"Failed to create default Groq client: {e}")

except ImportError:
    logger.warning("Groq package not found. Groq models will not be available.")
    
    def get_groq_client():
        raise ImportError("Groq package is not installed. Unable to create Groq client.")