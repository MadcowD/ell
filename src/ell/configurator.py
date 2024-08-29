from functools import wraps
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
import openai
import logging
from contextlib import contextmanager
import threading
from ell.store import Store

_config_logger = logging.getLogger(__name__)

@dataclass
class _Config:
    model_registry: Dict[str, openai.Client] = field(default_factory=dict)
    verbose: bool = False
    wrapped_logging: bool = True
    override_wrapped_logging_width: Optional[int] = None
    _store: Optional[Store] = None
    autocommit: bool = False
    lazy_versioning : bool = True # Optimizes computation of versionoing to the initial invocaiton
    # XXX: This might lead to incorrect serialization of globals/
    default_lm_params: Dict[str, Any] = field(default_factory=dict)
    default_system_prompt: str = "You are a helpful AI assistant."
    _default_openai_client: Optional[openai.Client] = None

    def __post_init__(self):
        self._lock = threading.Lock()
        self._local = threading.local()

    def register_model(self, model_name: str, client: openai.Client) -> None:
        with self._lock:
            self.model_registry[model_name] = client

    @property 
    def has_store(self) -> bool:
        return self._store is not None

    @contextmanager
    def model_registry_override(self, overrides: Dict[str, openai.Client]):
        if not hasattr(self._local, 'stack'):
            self._local.stack = []
        
        with self._lock:
            current_registry = self._local.stack[-1] if self._local.stack else self.model_registry
            new_registry = current_registry.copy()
            new_registry.update(overrides)
        
        self._local.stack.append(new_registry)
        try:
            yield
        finally:
            self._local.stack.pop()

    def get_client_for(self, model_name: str) -> Optional[openai.Client]:
        current_registry = self._local.stack[-1] if hasattr(self._local, 'stack') and self._local.stack else self.model_registry
        client = current_registry.get(model_name)
        if client is None:
            warning_message = f"Warning: A defualt provider for model '{model_name}' could not be found. Falling back to default OpenAI client from environment variables."
            if self.verbose:
                from colorama import Fore, Style
                _config_logger.warning(f"{Fore.LIGHTYELLOW_EX}{warning_message}{Style.RESET_ALL}")
            else:
                _config_logger.debug(warning_message)
            client = self._default_openai_client
        
        return client

    def reset(self) -> None:
        with self._lock:
            self.__init__()
            if hasattr(self._local, 'stack'):
                del self._local.stack
    
    def set_store(self, store: Union[Store, str], autocommit: bool = True) -> None:
        if isinstance(store, str):
            from ell.stores.sql import SQLiteStore
            self._store = SQLiteStore(store)
        else:
            self._store = store
        self.autocommit = autocommit or self.autocommit

    def get_store(self) -> Store:
        return self._store
    
    def set_default_lm_params(self, **params: Dict[str, Any]) -> None:
        self.default_lm_params = params
    
    def set_default_system_prompt(self, prompt: str) -> None:
        self.default_system_prompt = prompt

    def set_default_client(self, client: openai.Client) -> None:
        self.default_client = client


# Singleton instance
config = _Config()

def init(
    store: Optional[Union[Store, str]] = None,
    verbose: bool = False,
    autocommit: bool = True,
    lazy_versioning: bool = True,
    default_lm_params: Optional[Dict[str, Any]] = None,
    default_system_prompt: Optional[str] = None,
    default_openai_client: Optional[openai.Client] = None
) -> None:
    """
    Initialize the ELL configuration with various settings.

    Args:
        verbose (bool): Set verbosity of ELL operations.
        store (Union[Store, str], optional): Set the store for ELL. Can be a Store instance or a string path for SQLiteStore.
        autocommit (bool): Set autocommit for the store operations.
        lazy_versioning (bool): Enable or disable lazy versioning.
        default_lm_params (Dict[str, Any], optional): Set default parameters for language models.
        default_system_prompt (str, optional): Set the default system prompt.
        default_openai_client (openai.Client, optional): Set the default OpenAI client.
    """
    config.verbose = verbose
    config.lazy_versioning = lazy_versioning

    if store is not None:
        config.set_store(store, autocommit)

    if default_lm_params is not None:
        config.set_default_lm_params(**default_lm_params)

    if default_system_prompt is not None:
        config.set_default_system_prompt(default_system_prompt)

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

@wraps(config.set_default_system_prompt)
def set_default_system_prompt(*args, **kwargs) -> None:
    return config.set_default_system_prompt(*args, **kwargs)

# You can add more helper functions here if needed
