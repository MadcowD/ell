from contextlib import contextmanager
from typing import Optional, Callable, Any

from ell.types import InvocableLM


# __is_caching_functions = {}
# __cache_except = {}


@contextmanager
def cache(*lmps : InvocableLM):
    """
    A context manager for caching operations.

    Args:
        key (Optional[str]): The cache key. If None, a default key will be generated.
        condition (Optional[Callable[..., bool]]): A function that determines whether to cache or not.

    Yields:
        None
    """
    old_cache_values = {}
    try:
        for lmp in lmps:
            old_cache_values[lmp] = getattr(lmp, '__ell_use_cache', False)
            lmp.__ell_use_cache = True
        yield
    finally:
        # TODO: Implement cache storage logic here
        for lmp in lmps:
            lmp.__ell_use_cache = old_cache_values.get(lmp, False)

@contextmanager
def cache_except(*lmps : InvocableLM):
    """
    A context manager for caching operations, except when specified exceptions occur.

    Args:
        *exceptions: Exception types that should not be cached.

    Yields:
        None
    """
    try:
        # TODO: Implement cache lookup logic here
        # TODO: This is why we actually dont want to store the cache on the function.
        yield
    finally:
        pass
    




