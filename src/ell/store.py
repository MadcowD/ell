from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional, Dict, List, Set, Union
from ell.lstr import lstr
from ell.types import InvocableLM, SerializedLMP, Invocation, SerializedLStr


class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

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
    def write_invocation(self, invocation: Invocation, results: List[SerializedLStr], consumes: Set[str]) -> Optional[Any]:
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

    # @abstractmethod
    # def get_lmps(self, skip: int = 0, limit: int = 10, subquery=None, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """
    #     Retrieve LMPs from the storage.

    #     :param skip: Number of records to skip.
    #     :param limit: Maximum number of records to return.
    #     :param subquery: Optional subquery for filtering.
    #     :param filters: Optional dictionary of filters to apply.
    #     :return: List of LMPs.
    #     """
    #     pass

    # @abstractmethod
    # def get_invocations(self, lmp_filters: Dict[str, Any], skip: int = 0, limit: int = 10, filters: Optional[Dict[str, Any]] = None, hierarchical: bool = False) -> List[Dict[str, Any]]:
    #     """
    #     Retrieve invocations of an LMP from the storage.

    #     :param lmp_filters: Filters to apply on the LMP level.
    #     :param skip: Number of records to skip.
    #     :param limit: Maximum number of records to return.
    #     :param filters: Optional dictionary of filters to apply on the invocation level.
    #     :param hierarchical: Whether to include hierarchical information.
    #     :return: List of invocations.
    #     """
    #     pass

    # @abstractmethod
    # def get_latest_lmps(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    #     """
    #     Retrieve the latest versions of all LMPs from the storage.

    #     :param skip: Number of records to skip.
    #     :param limit: Maximum number of records to return.
    #     :return: List of the latest LMPs.
    #     """
    #     pass

    # @abstractmethod
    # def get_traces(self) -> List[Dict[str, Any]]:
    #     """
    #     Retrieve all traces from the storage.

    #     :return: List of traces.
    #     """
    #     pass

    # @abstractmethod
    # def get_all_traces_leading_to(self, invocation_id: str) -> List[Dict[str, Any]]:
    #     """
    #     Retrieve all traces leading to a specific invocation.

    #     :param invocation_id: ID of the invocation to trace.
    #     :return: List of traces leading to the specified invocation.
    #     """
    #     pass

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