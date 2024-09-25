from functools import lru_cache, wraps
from typing import Dict, Any, Optional, Tuple, Union, Type
import openai
import logging
from contextlib import contextmanager
import threading
from pydantic import BaseModel, ConfigDict, Field
from ell.store import Store
from ell.provider import Provider
from dataclasses import dataclass, field

_config_logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class _Model:
    name: str
    default_client: Optional[Union[openai.Client, Any]] = None
    #XXX: Deprecation in 0.1.0
    #XXX: We will depreciate this when streaming is implemented. 
    # Currently we stream by default for the verbose renderer,
    # but in the future we will not support streaming by default 
    # and stream=True must be passed which will then make API providers the
    # single source of truth for whether or not a model supports an api parameter.
    # This makes our implementation extremely light, only requiring us to provide
    # a list of model names in registration.
    supports_streaming : Optional[bool] = field(default=None)



class Config(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    registry: Dict[str, _Model] = Field(default_factory=dict, description="A dictionary mapping model names to their configurations.")
    verbose: bool = Field(default=False, description="If True, enables verbose logging.")
    wrapped_logging: bool = Field(default=True, description="If True, enables wrapped logging for better readability.")
    override_wrapped_logging_width: Optional[int] = Field(default=None, description="If set, overrides the default width for wrapped logging.")
    store: Optional[Store] = Field(default=None, description="An optional Store instance for persistence.")
    autocommit: bool = Field(default=False, description="If True, enables automatic committing of changes to the store.")
    lazy_versioning: bool = Field(default=True, description="If True, enables lazy versioning for improved performance.")
    default_api_params: Dict[str, Any] = Field(default_factory=dict, description="Default parameters for language models.")
    default_client: Optional[openai.Client] = Field(default=None, description="The default OpenAI client used when a specific model client is not found.")
    providers: Dict[Type, Provider] = Field(default_factory=dict, description="A dictionary mapping client types to provider classes.")
    def __init__(self, **data):
        super().__init__(**data)
        self._lock = threading.Lock()
        self._local = threading.local()

    
    def register_model(
        self, 
        name: str,
        default_client: Optional[Union[openai.Client, Any]] = None,
        supports_streaming: Optional[bool] = None
    ) -> None:
        """
        Register a model with its configuration.
        """
        with self._lock:
            # XXX: Will be deprecated in 0.1.0
            self.registry[name] = _Model(
                name=name,
                default_client=default_client,
                supports_streaming=supports_streaming
            )



    @contextmanager
    def model_registry_override(self, overrides: Dict[str, _Model]):
        """
        Temporarily override the model registry with new model configurations.

        :param overrides: A dictionary of model names to ModelConfig instances to override.
        :type overrides: Dict[str, ModelConfig]
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

    def get_client_for(self, model_name: str) -> Tuple[Optional[openai.Client], bool]:
        """
        Get the OpenAI client for a specific model name.

        :param model_name: The name of the model to get the client for.
        :type model_name: str
        :return: The OpenAI client for the specified model, or None if not found, and a fallback flag.
        :rtype: Tuple[Optional[openai.Client], bool]
        """
        current_registry = self._local.stack[-1] if hasattr(self._local, 'stack') and self._local.stack else self.registry
        model_config = current_registry.get(model_name)
        fallback = False
        if not model_config:
            warning_message = f"Warning: A default provider for model '{model_name}' could not be found. Falling back to default OpenAI client from environment variables."
            if self.verbose:
                from colorama import Fore, Style
                _config_logger.warning(f"{Fore.LIGHTYELLOW_EX}{warning_message}{Style.RESET_ALL}")
            else:
                _config_logger.debug(warning_message)
            client = self.default_client
            fallback = True
        else:
            client = model_config.default_client
        return client, fallback

    def register_provider(self, provider: Provider, client_type: Type[Any]) -> None:
        """
        Register a provider class for a specific client type.

        :param provider_class: The provider class to register.
        :type provider_class: Type[Provider]
        """
        assert isinstance(client_type, type), "client_type must be a type (e.g. openai.Client), not an an instance (myclient := openai.Client()))"
        with self._lock:
            self.providers[client_type] = provider

    def get_provider_for(self, client: Union[Type[Any], Any]) -> Optional[Provider]:
        """
        Get the provider instance for a specific client instance.

        :param client: The client instance to get the provider for.
        :type client: Any
        :return: The provider instance for the specified client, or None if not found.
        :rtype: Optional[Provider]
        """

        client_type = type(client) if not isinstance(client, type) else client
        for provider_type, provider in self.providers.items():
            if issubclass(client_type, provider_type) or client_type == provider_type:
                return provider
        return None

# Single* instance
# XXX: Make a singleton
config = Config()

def init(
    store: Optional[Union[Store, str]] = None,
    verbose: bool = False,
    autocommit: bool = True,
    lazy_versioning: bool = True,
    default_api_params: Optional[Dict[str, Any]] = None,
    default_client: Optional[Any] = None
) -> None:
    """
    Initialize the ELL configuration with various settings.

    :param verbose: Set verbosity of ELL operations.
    :type verbose: bool
    :param store: Set the store for ELL. Can be a Store instance or a string path for SQLiteStore.
    :type store: Union[Store, str], optional
    :param autocommit: Set autocommit for the store operations.
    :type autocommit: bool
    :param lazy_versioning: Enable or disable lazy versioning.
    :type lazy_versioning: bool
    :param default_api_params: Set default parameters for language models.
    :type default_api_params: Dict[str, Any], optional
    :param default_openai_client: Set the default OpenAI client.
    :type default_openai_client: openai.Client, optional
    """
    # XXX: prevent double init
    config.verbose = verbose
    config.lazy_versioning = lazy_versioning

    if isinstance(store, str):
        from ell.stores.sql import SQLiteStore
        config.store = SQLiteStore(store)
    else:
        config.store = store
    config.autocommit = autocommit or config.autocommit

    if default_api_params is not None:
        config.default_api_params.update(default_api_params)

    if default_client is not None:
        config.default_client = default_client

# Existing helper functions
def get_store() -> Union[Store, None]:
    return config.store

# Will be deprecated at 0.1.0 

# You can add more helper functions here if needed
def register_provider(provider: Provider, client_type: Type[Any]) -> None:
    return config.register_provider(provider, client_type)

# Deprecated now (remove at 0.1.0)
def set_store(*args, **kwargs) -> None:
    raise DeprecationWarning("The set_store function is deprecated and will be removed in a future version. Use ell.init(store=...) instead.")