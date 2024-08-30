from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional, Dict, List, Set, Union
from ell.types._lstr import _lstr
from ell.types import SerializedLMP, Invocation
from ell.types.message import InvocableLM

class BlobStore(ABC):
    @abstractmethod
    def store_blob(self, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a blob and return its identifier."""
        pass

    @abstractmethod
    def retrieve_blob(self, blob_id: str) -> bytes:
        """Retrieve a blob by its identifier."""
        pass

class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

    def __init__(self, blob_store: Optional[BlobStore] = None):
        self.blob_store = blob_store

    @property
    def has_blob_storage(self) -> bool:
        return self.blob_store is not None

    @abstractmethod
    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        """
        Write an LMP (Language Model Package) to the storage.

        :param serialized_lmp: SerializedLMP object containing all LMP details.
        :param uses: Dictionary of LMPs used by this LMP.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def write_invocation(self, invocation: Invocation,  consumes: Set[str]) -> Optional[Any]:
        """
        Write an invocation of an LMP to the storage.

        :param invocation: Invocation object containing all invocation details.
        :param results: List of SerializedLStr objects representing the results.
        :param consumes: Set of invocation IDs consumed by this invocation.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def get_cached_invocations(self, lmp_id :str, state_cache_key :str) -> List[Invocation]:
        """
        Get cached invocations for a given LMP and state cache key.
        """
        pass

    @abstractmethod
    def get_versions_by_fqn(self, fqn :str) -> List[SerializedLMP]:
        """
        Get all versions of an LMP by its fully qualified name.
        """
        pass


    @contextmanager
    def freeze(self, *lmps: InvocableLM):
        """
        A context manager for caching operations using a particular store.

        Args:
            *lmps: InvocableLM objects to freeze.

        Yields:
            None
        """
        old_cache_values = {}
        try:
            for lmp in lmps:
                old_cache_values[lmp] = getattr(lmp, '__ell_use_cache__', None)
                setattr(lmp, '__ell_use_cache__', self)
            yield
        finally:
            # TODO: Implement cache storage logic here
            for lmp in lmps:
                if lmp in old_cache_values:
                    setattr(lmp, '__ell_use_cache__', old_cache_values[lmp])
                else:
                    delattr(lmp, '__ell_use_cache__')