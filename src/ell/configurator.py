from functools import wraps
from typing import Dict, Any, Optional, Tuple, Union, Type
import openai
import logging
from contextlib import contextmanager
import threading
from pydantic import BaseModel, ConfigDict, Field
from ell.api.client import EllAPIClient, EllClient, EllSqliteClient
from ell.provider import Provider

_config_logger = logging.getLogger(__name__)


class Config(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    registry: Dict[str, openai.Client] = Field(default_factory=dict, description="A dictionary mapping model names to OpenAI clients.")
    verbose: bool = Field(default=False, description="If True, enables wrapped logging for better readability.")
    wrapped_logging: bool = Field(default=True, description="If True, enables wrapped logging for better readability.")
    override_wrapped_logging_width: Optional[int] = Field(default=None, description="If set, overrides the default width for wrapped logging.")
    autocommit: bool = Field(default=False, description="If True, enables automatic committing of changes to the store.")
    lazy_versioning: bool = Field(default=True, description="If True, enables lazy versioning for improved performance.")
    default_lm_params: Dict[str, Any] = Field(default_factory=dict, description="Default parameters for language models.")
    default_system_prompt: str = Field(default="You are a helpful AI assistant.", description="The default system prompt used for AI interactions.")
    default_client: Optional[openai.Client] = Field(default=None, description="The default OpenAI client used when a specific model client is not found.")
    providers: Dict[Type, Type[Provider]] = Field(default_factory=dict, description="A dictionary mapping client types to provider classes.")
    default_openai_client: Optional[openai.Client] = Field(default=None, description="The default OpenAI client used when a specific model client is not found.")
    _client: Optional[EllClient] = None
    store_blobs: bool = Field(default=True, description="If True, enables storing blobs in the store.")



    def __init__(self, **data):
        super().__init__(**data)
        self._lock = threading.Lock()
        self._local = threading.local()

    def register_model(self, model_name: str, client: Any) -> None:
        """
        Register an OpenAI client for a specific model name.

        :param model_name: The name of the model to register.
        :type model_name: str
        :param client: The OpenAI client to associate with the model.
        :type client: openai.Client
        """
        with self._lock:
            self.registry[model_name] = client


    @contextmanager
    def model_registry_override(self, overrides: Dict[str, Any]):
        """
        Temporarily override the model registry with new client mappings.

        :param overrides: A dictionary of model names to OpenAI clients to override.
        :type overrides: Dict[str, openai.Client]
        """
        if not hasattr(self._local, 'stack'):
            self._local.stack = []

        with self._lock:
            current_registry = self._local.stack[-1] if self._local.stack else self.registry
            new_registry = current_registry.copy()
            new_registry.update(overrides)

        self._local.stack.append(new_registry)
        try:
            yield
        finally:
            self._local.stack.pop()

    def get_client_for(self, model_name: str) -> Tuple[Optional[Any], bool]:
        """
        Get the OpenAI client for a specific model name.

        :param model_name: The name of the model to get the client for.
        :type model_name: str
        :return: The OpenAI client for the specified model, or None if not found.
        :rtype: Optional[openai.Client]
        """
        current_registry = self._local.stack[-1] if hasattr(
            self._local, 'stack') and self._local.stack else self.registry
        client = current_registry.get(model_name)
        fallback = False
        if model_name not in current_registry.keys():
            warning_message = (f"Warning: A default provider for model '{model_name}' "
                               "could not be found. Falling back to default OpenAI "
                               "client from environment variables.")
            if self.verbose:
                from colorama import Fore, Style
                _config_logger.warning(f"{Fore.LIGHTYELLOW_EX}{warning_message}{Style.RESET_ALL}")
            else:
                _config_logger.debug(warning_message)
            client = self.default_openai_client
            fallback = True
        return client, fallback

    def reset(self) -> None:
        """
        Reset the configuration to its initial state.
        """
        with self._lock:
            self.__init__()
            if hasattr(self._local, 'stack'):
                del self._local.stack

    def set_default_lm_params(self, **params: Dict[str, Any]) -> None:
        """
        Set default parameters for language models.

        :param params: Keyword arguments representing the default parameters.
        :type params: Dict[str, Any]
        """
        self.default_lm_params = params

    def set_default_client(self, client: openai.Client) -> None:
        """
        Set the default OpenAI client.

        :param client: The default OpenAI client to set.
        :type client: openai.Client
        """
        self.default_openai_client = client

    def set_ell_client(self, client: EllClient) -> None:
        self._client = client

    def register_provider(self, provider_class: Type[Provider]) -> None:
        """
        Register a provider class for a specific client type.

        :param provider_class: The provider class to register.
        :type provider_class: Type[AbstractProvider]
        """
        with self._lock:
            self.providers[provider_class.get_client_type()] = provider_class

    def get_provider_for(self, client: Any) -> Optional[Type[Provider]]:
        """
        Get the provider class for a specific client instance.

        :param client: The client instance to get the provider for.
        :type client: Any
        :return: The provider class for the specified client, or None if not found.
        :rtype: Optional[Type[AbstractProvider]]
        """
        return next((provider for client_type, provider in self.providers.items() if isinstance(client, client_type)), None)

# Singleton instance
config = Config()


def init(
    client: Optional[EllClient] = None,
    base_url: Optional[str] = None,
    storage_dir: Optional[str] = None,
    store_blobs: bool = True,
    verbose: bool = False,
    autocommit: bool = True,
    lazy_versioning: bool = True,
    default_lm_params: Optional[Dict[str, Any]] = None,
    default_openai_client: Optional[openai.Client] = None
) -> None:
    """
    Initialize the ELL configuration with various settings.

    :param verbose: Set verbosity of ELL operations.
    :type verbose: bool
    :param storage_dir: Set the storage directory.
    :type storage_dir: str
    :param autocommit: Set autocommit for the store operations.
    :type autocommit: bool
    :param lazy_versioning: Enable or disable lazy versioning.
    :type lazy_versioning: bool
    :param default_lm_params: Set default parameters for language models.
    :type default_lm_params: Dict[str, Any], optional
    :param default_openai_client: Set the default OpenAI client.
    :type default_openai_client: openai.Client, optional
    """
    config.verbose = verbose
    config.store_blobs = store_blobs
    config.lazy_versioning = lazy_versioning
    config.autocommit = autocommit

    if client is not None:
        config.set_ell_client(client)
    elif base_url is not None:
        config.set_ell_client(EllAPIClient(base_url))
    elif storage_dir is not None:
        config.set_ell_client(EllSqliteClient(storage_dir))

    if default_lm_params is not None:
        config.set_default_lm_params(**default_lm_params)

    if default_openai_client is not None:
        config.set_default_client(default_openai_client)

# Existing helper functions
@wraps(config.set_default_lm_params)
def set_default_lm_params(*args, **kwargs) -> None:
    return config.set_default_lm_params(*args, **kwargs)

# You can add more helper functions here if needed
@wraps(config.register_provider)
def register_provider(*args, **kwargs) -> None:
    return config.register_provider(*args, **kwargs)