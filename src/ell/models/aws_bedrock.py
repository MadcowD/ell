from ell.configurator import config
import logging

logger = logging.getLogger(__name__)


try:
    import boto3

    def register(client: boto3.Client):
        """
        Register Bedrock models with the provided client.

        This function takes an boto3 client and registers various Bedrock models
        with the global configuration. It allows the system to use these models
        for different AI tasks.

        Args:
            client (boto3.Client): An instance of the bedrock client to be used
                                          for model registration.

        Note:
            The function doesn't return anything but updates the global
            configuration with the registered models.
        """
        model_data = [
            ('anthropic.claude-3-opus-20240229-v1:0', 'aws_bedrock'),
            ('anthropic.claude-3-sonnet-20240229-v1:0', 'aws_bedrock'),
            ('anthropic.claude-3-haiku-20240307-v1:0', 'aws_bedrock'),
            ('anthropic.claude-3-5-sonnet-20240620-v1:0', 'aws_bedrock'),

            ('mistral.mistral-7b-instruct-v0:2', 'aws_bedrock'),
            ('mistral.mixtral-8x7b-instruct-v0:1', 'aws_bedrock'),

        ]
        for model_id, owned_by in model_data:
            config.register_model(model_id, client)

    try:
        print('BEDROCKKKKKKK')
        default_client = boto3.client('bedrock-runtime')
        register(default_client)
    except Exception as e:
        # logger.warning(f"Failed to create default bedrock client: {e}")
        pass


except ImportError:
    pass