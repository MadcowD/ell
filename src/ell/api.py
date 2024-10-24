from ell.configurator import config
from ell.ctxt import get_session_id
from typing import Dict, List, Optional, Set, Any
from ell.types import SerializedLMP, Invocation, InvocationContents

def write_lmp(serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[SerializedLMP]:
    """
    Write a serialized LMP to the store.

    :param serialized_lmp: The SerializedLMP object to write.
    :param uses: A dictionary of LMPs that this LMP uses.
    :return: The written LMP or None if it already exists.
    """
    return config.store.write_lmp(serialized_lmp, uses)

def write_invocation(invocation: Invocation, consumes: Set[str]) -> Optional[Any]:
    """
    Write an invocation to the store.

    :param invocation: The Invocation object to write.
    :param consumes: A set of invocation IDs that this invocation consumes.
    :return: None
    """
    return config.store.write_invocation(invocation, consumes)

def get_invocations_by_session_id(session_id: str = "") -> List[Invocation]:
    """
    Retrieve invocations by session ID.

    :param session_id: The session ID to filter by.
    :return: A list of Invocation objects.
    """
    session_id = session_id or get_session_id()
    return config.store.get_invocations_by_sessionid(session_id)

def get_cached_invocations(lmp_id: str, state_cache_key: str) -> List[Invocation]:
    """
    Retrieve cached invocations for a given LMP and state cache key.

    :param lmp_id: The ID of the LMP.
    :param state_cache_key: The state cache key.
    :return: A list of Invocation objects.
    """
    return config.store.get_cached_invocations(lmp_id, state_cache_key)

def get_cached_invocations_contents(lmp_id: str, state_cache_key: str) -> List[InvocationContents]:
    """
    Retrieve contents of cached invocations for a given LMP and state cache key.

    :param lmp_id: The ID of the LMP.
    :param state_cache_key: The state cache key.
    :return: A list of InvocationContents objects.
    """
    return config.store.get_cached_invocations_contents(lmp_id, state_cache_key)

def get_lmp(lmp_id: str) -> Optional[SerializedLMP]:
    """
    Retrieve an LMP by its ID.

    :param lmp_id: The ID of the LMP to retrieve.
    :return: A SerializedLMP object or None if not found.
    """
    return config.store.get_lmp(lmp_id)

def get_versions_by_fqn(fqn: str) -> List[SerializedLMP]:
    """
    Retrieve all versions of an LMP by its fully qualified name.

    :param fqn: The fully qualified name of the LMP.
    :return: A list of SerializedLMP objects.
    """
    return config.store.get_versions_by_fqn(fqn)

def get_latest_lmps(skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve the latest LMPs.

    :param skip: Number of records to skip.
    :param limit: Maximum number of records to return.
    :return: A list of SerializedLMP objects.
    """
    with config.store.engine.begin() as session:
        return config.store.get_latest_lmps(session, skip, limit)

def get_lmps(skip: int = 0, limit: int = 10, **filters: Any) -> List[Dict[str, Any]]:
    """
    Retrieve LMPs based on filters.

    :param skip: Number of records to skip.
    :param limit: Maximum number of records to return.
    :param filters: Additional filters to apply.
    :return: A list of SerializedLMP objects.
    """
    with config.store.engine.begin() as session:
        return config.store.get_lmps(session, skip, limit, **filters)

def get_invocations(lmp_filters: Dict[str, Any], skip: int = 0, limit: int = 10, filters: Optional[Dict[str, Any]] = None, hierarchical: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve invocations based on filters.

    :param lmp_filters: Filters to apply to the LMP.
    :param skip: Number of records to skip.
    :param limit: Maximum number of records to return.
    :param filters: Additional filters to apply to the invocation.
    :param hierarchical: Whether to return hierarchical results.
    :return: A list of Invocation objects.
    """
    with config.store.engine.begin() as session:
        return config.store.get_invocations(session, lmp_filters, skip, limit, filters, hierarchical)

def get_traces() -> List[Dict[str, Any]]:
    """
    Retrieve all traces.

    :return: A list of trace dictionaries.
    """
    with config.store.engine.begin() as session:
        return config.store.get_traces(session)

def get_invocations_aggregate(lmp_filters: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, days: int = 30) -> Dict[str, Any]:
    """
    Retrieve aggregate data for invocations.

    :param lmp_filters: Filters to apply to the LMP.
    :param filters: Additional filters to apply to the invocation.
    :param days: Number of days to include in the aggregation.
    :return: A dictionary containing aggregate data and graph data.
    """
    with config.store.engine.begin() as session:
        return config.store.get_invocations_aggregate(session, lmp_filters, filters, days)
