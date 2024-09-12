from ell.configurator import config
import logging

logger = logging.getLogger(__name__)


try:
    import anthropic

    def register(client: anthropic.Anthropic):
        """
        Register Anthropic models with the provided client.

        This function takes an Anthropic client and registers various Anthropic models
        with the global configuration. It allows the system to use these models
        for different AI tasks.

        Args:
            client (anthropic.Anthropic): An instance of the Anthropic client to be used
                                          for model registration.

        Note:
            The function doesn't return anything but updates the global
            configuration with the registered models.
        """
        model_data = [
            ('claude-3-opus-20240229', 'anthropic'),
            ('claude-3-sonnet-20240229', 'anthropic'),
            ('claude-3-haiku-20240307', 'anthropic'),
            ('claude-3-5-sonnet-20240620', 'anthropic'),
        ]
        for model_id, owned_by in model_data:
            config.register_model(model_id, client)

    try:
        default_client = anthropic.Anthropic()
        register(default_client)
    except Exception as e:
        # logger.warning(f"Failed to create default Anthropic client: {e}")
        pass


except ImportError:
    pass