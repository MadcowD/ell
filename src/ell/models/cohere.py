from ell.configurator import config
import logging

logger = logging.getLogger(__name__)

try:
    import cohere

    def register(client: cohere.Client):
        """
        Register Cohere models with the provided client.
        """
        model_data = [
            ('command-r-plus-08-2024', 'cohere'),
            ('command-r', 'cohere'),
            ('command-r-plus', 'cohere'),
            ('command-r-08-2024', 'cohere'),
        ]
        for model_id, owned_by in model_data:
            config.register_model(model_id, client)

    try:
        default_client = cohere.Client()
        register(default_client)
    except Exception as e:
        #logger.warning(f"Failed to create default Cohere client: {e}")
        # This does give a warning. 
        # status_code: None, body: The client must be instantiated be either passing in token or setting CO_API_KEY
        pass

except ImportError:
    pass