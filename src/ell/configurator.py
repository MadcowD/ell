from functools import wraps
from typing import Dict, Any, Optional, Tuple, Union, Type
import openai
import logging
from contextlib import contextmanager
import threading
from pydantic import BaseModel, ConfigDict, Field
from ell.store import Store
from ell.provider import Provider

_config_logger = logging.getLogger(__name__)
class Config(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    registry: Dict[str, openai.Client] = Field(default_factory=dict, description="A dictionary mapping model names to OpenAI clients.")
    verbose: bool = Field(default=False, description="If True, enables verbose logging.")
    wrapped_logging: bool = Field(default=True, description="If True, enables wrapped logging for better readability.")
    override_wrapped_logging_width: Optional[int] = Field(default=None, description="If set, overrides the default width for wrapped logging.")
    store: Optional[Store] = Field(default=None, description="An optional Store instance for persistence.")
    autocommit: bool = Field(default=False, description="If True, enables automatic committing of changes to the store.")
    lazy_versioning: bool = Field(default=True, description="If True, enables lazy versioning for improved performance.")
    default_lm_params: Dict[str, Any] = Field(default_factory=dict, description="Default parameters for language models.")
    default_client: Optional[openai.Client] = Field(default=None, description="The default OpenAI client used when a specific model client is not found.")
    providers: Dict[Type, Type[Provider]] = Field(default_factory=dict, description="A dictionary mapping client types to provider classes.")

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

    @property 
    def has_store(self) -> bool:
        """
        Check if a store is set.

        :return: True if a store is set, False otherwise.
        :rtype: bool
        """
        return self.store is not None

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
        current_registry = self._local.stack[-1] if hasattr(self._local, 'stack') and self._local.stack else self.registry
        client = current_registry.get(model_name)
        fallback = False
        if model_name not in current_registry.keys():
            warning_message = f"Warning: A default provider for model '{model_name}' could not be found. Falling back to default OpenAI client from environment variables."
            if self.verbose:
                from colorama import Fore, Style
                _config_logger.warning(f"{Fore.LIGHTYELLOW_EX}{warning_message}{Style.RESET_ALL}")
            else:
                _config_logger.debug(warning_message)
            client = self.default_client
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
    
    def set_store(self, store: Union[Store, str], autocommit: bool = True) -> None:
        """
        Set the store for the configuration.

        :param store: The store to set. Can be a Store instance or a string path for SQLiteStore.
        :type store: Union[Store, str]
        :param autocommit: Whether to enable autocommit for the store.
        :type autocommit: bool
        """
        if isinstance(store, str):
            from ell.stores.sql import SQLiteStore
            self.store = SQLiteStore(store)
        else:
            self.store = store
        self.autocommit = autocommit or self.autocommit

    def get_store(self) -> Store:
        """
        Get the current store.

        :return: The current store.
        :rtype: Store
        """
        return self.store
    
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
        self.default_client = client

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
    store: Optional[Union[Store, str]] = None,
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
    :param store: Set the store for ELL. Can be a Store instance or a string path for SQLiteStore.
    :type store: Union[Store, str], optional
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
    config.lazy_versioning = lazy_versioning

    if store is not None:
        config.set_store(store, autocommit)

    if default_lm_params is not None:
        config.set_default_lm_params(**default_lm_params)



    if default_openai_client is not None:
        config.set_default_client(default_openai_client)

# Existing helper functions
@wraps(config.get_store)
def get_store() -> Store:
    return config.get_store()

@wraps(config.set_store)
def set_store(*args, **kwargs) -> None:
    return config.set_store(*args, **kwargs)

@wraps(config.set_default_lm_params)
def set_default_lm_params(*args, **kwargs) -> None:
    return config.set_default_lm_params(*args, **kwargs)

# You can add more helper functions here if needed
@wraps(config.register_provider)
def register_provider(*args, **kwargs) -> None:
    return config.register_provider(*args, **kwargs)