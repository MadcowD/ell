from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional, Dict, List, Set, Union
from ell.lstr import lstr
from ell.types import InvocableLM


class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

    @abstractmethod
    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str, 
                  version_number: int,
                  uses: Dict[str, Any], 
                  commit_message: Optional[str] = None,
                  created_at: Optional[float]=None) -> Optional[Any]:
        """
        Write an LMP (Language Model Package) to the storage.

        :param lmp_id: Unique identifier for the LMP.
        :param name: Name of the LMP.
        :param source: Source code or reference for the LMP.
        :param dependencies: List of dependencies for the LMP.
        :param is_lmp: Boolean indicating if it is an LMP.
        :param lm_kwargs: Additional keyword arguments for the LMP.
        :param uses: Dictionary of LMPs used by this LMP.
        :param created_at: Optional timestamp of when the LMP was created.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any], 
                         created_at: Optional[float], consumes: Set[str], prompt_tokens: Optional[int] = None,
                         completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,
                         state_cache_key: Optional[str] = None,
                         cost_estimate: Optional[float] = None) -> Optional[Any]:
        """
        Write an invocation of an LMP to the storage.

        :param id: Unique identifier for the invocation.
        :param lmp_id: Unique identifier for the LMP.
        :param args: Arguments used in the invocation.
        :param kwargs: Keyword arguments used in the invocation.
        :param result: Result of the invocation.
        :param invocation_kwargs: Additional keyword arguments for the invocation.
        :param created_at: Optional timestamp of when the invocation was created.
        :param consumes: Set of invocation IDs consumed by this invocation.
        :param prompt_tokens: Optional number of prompt tokens used.
        :param completion_tokens: Optional number of completion tokens used.
        :param latency_ms: Optional latency in milliseconds.
        :param cost_estimate: Optional estimated cost of the invocation.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve LMPs from the storage.

        :param filters: Optional dictionary of filters to apply.
        :return: List of LMPs.
        """
        pass

    @abstractmethod
    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve invocations of an LMP from the storage.

        :param lmp_id: Unique identifier for the LMP.
        :param filters: Optional dictionary of filters to apply.
        :return: List of invocations.
        """
        pass

    # @abstractmethod
    # def search_lmps(self, query: str) -> List[Dict[str, Any]]:
    #     """
    #     Search for LMPs in the storage.

    #     :param query: Search query string.
    #     :return: List of LMPs matching the query.
    #     """
    #     pass

    # @abstractmethod
    # def search_invocations(self, query: str) -> List[Dict[str, Any]]:
    #     """
    #     Search for invocations in the storage.

    #     :param query: Search query string.
    #     :return: List of invocations matching the query.
    #     """
    #     pass

    @abstractmethod
    def get_lmp_versions(self, lmp_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all versions of an LMP from the storage.

        :param lmp_id: Unique identifier for the LMP.
        :return: List of LMP versions.
        """
        pass

    @abstractmethod
    def get_latest_lmps(self) -> List[Dict[str, Any]]:
        """
        Retrieve the latest versions of all LMPs from the storage.

        :return: List of the latest LMPs.
        """
        pass


    @contextmanager
    def freeze(self, *lmps: InvocableLM):
        """
        A context manager for caching operations using a particular store.

        Args:
            key (Optional[str]): The cache key. If None, a default key will be generated.
            condition (Optional[Callable[..., bool]]): A function that determines whether to cache or not.

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