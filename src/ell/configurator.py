from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
import openai
import logging
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

@dataclass
class _Config:
    model_registry: Dict[str, openai.Client] = field(default_factory=dict)
    verbose: bool = False
    wrapped_logging: bool = True
    override_wrapped_logging_width: Optional[int] = None
    store: Optional["Store"] = None
    autocommit: bool = False

    def __post_init__(self):
        self._lock = threading.Lock()
        self._local = threading.local()

    def register_model(self, model_name: str, client: openai.Client) -> None:
        with self._lock:
            self.model_registry[model_name] = client

    @property 
    def has_store(self) -> bool:
        return self.store is not None

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
            logger.warning(f"Model '{model_name}' is not registered. Falling back to OpenAI client from environment variables.")
        return client

    def reset(self) -> None:
        with self._lock:
            self.__init__()
            if hasattr(self._local, 'stack'):
                del self._local.stack

    def register_store(self, store: "Store", autocommit: bool = False) -> None:
        self.store = store
        self.autocommit = autocommit or self.autocommit

# Singleton instance
config = _Config()


def store() -> "Store":
    return config.store