import logging
import threading
from ell.types import SerializedLMP, Invocation, InvocationTrace, InvocationContents
from ell.types.studio import LMPType, utc_now
import ell.util.closure
from ell.configurator import config
from ell.types._lstr import _lstr

import inspect

import secrets
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Iterable, Optional, OrderedDict, Tuple

from ell.util.serialization import get_immutable_vars
from ell.util.serialization import compute_state_cache_key
from ell.util.serialization import prepare_invocation_params

logger = logging.getLogger(__name__)

# Thread-local storage for the invocation stack
_invocation_stack = threading.local()

def get_current_invocation() -> Optional[str]:
    if not hasattr(_invocation_stack, 'stack'):
        _invocation_stack.stack = []
    return _invocation_stack.stack[-1] if _invocation_stack.stack else None

def push_invocation(invocation_id: str):
    if not hasattr(_invocation_stack, 'stack'):
        _invocation_stack.stack = []
    _invocation_stack.stack.append(invocation_id)

def pop_invocation():
    if hasattr(_invocation_stack, 'stack') and _invocation_stack.stack:
        _invocation_stack.stack.pop()


def _track(func_to_track: Callable, *, forced_dependencies: Optional[Dict[str, Any]] = None) -> Callable:
        
    lmp_type = getattr(func_to_track, "__ell_type__", LMPType.OTHER)


    # see if it exists
    if not hasattr(func_to_track, "_has_serialized_lmp"):
        func_to_track._has_serialized_lmp = False

    if not hasattr(func_to_track, "__ell_hash__") and not config.lazy_versioning:
        ell.util.closure.lexically_closured_source(func_to_track, forced_dependencies)


    @wraps(func_to_track)
    def tracked_func(*fn_args, _get_invocation_id=False, **fn_kwargs) -> str:
        # XXX: Cache keys and global variable binding is not thread safe.
        # Compute the invocation id and hash the inputs for serialization.
        invocation_id = "invocation-" + secrets.token_hex(16)

        state_cache_key : str = None
        if not config.store:
            return func_to_track(*fn_args, **fn_kwargs, _invocation_origin=invocation_id)[0]

        parent_invocation_id = get_current_invocation()
        try:
            push_invocation(invocation_id)
 
            # Convert all positional arguments to named keyword arguments
            sig = inspect.signature(func_to_track)
            # Filter out kwargs that are not in the function signature
            filtered_kwargs = {k: v for k, v in fn_kwargs.items() if k in sig.parameters}
            
            bound_args = sig.bind(*fn_args, **filtered_kwargs)
            bound_args.apply_defaults()
            all_kwargs = dict(bound_args.arguments)

            # Get the list of consumed lmps and clean the invocation params for serialization.
            cleaned_invocation_params, ipstr, consumes = prepare_invocation_params( all_kwargs)

            try_use_cache = hasattr(func_to_track.__wrapper__, "__ell_use_cache__")

            if  try_use_cache:
                # Todo: add nice logging if verbose for when using a cahced invocaiton. IN a different color with thar args..
                if not hasattr(func_to_track, "__ell_hash__")  and config.lazy_versioning:
                    fn_closure, _ = ell.util.closure.lexically_closured_source(func_to_track)
                
                # compute the state cachekey
                state_cache_key = compute_state_cache_key(ipstr, func_to_track.__ell_closure__)
                
                cache_store = func_to_track.__wrapper__.__ell_use_cache__
                cached_invocations = cache_store.get_cached_invocations(func_to_track.__ell_hash__, state_cache_key)
                
        
                if len(cached_invocations) > 0:
                    # TODO THis is bad?
                    results =  [d.deserialize() for  d in cached_invocations[0].results]

                    logger.info(f"Using cached result for {func_to_track.__qualname__} with state cache key: {state_cache_key}")
                    if len(results) == 1:
                        return results[0]
                    else:
                        return results
                    # Todo: Unfiy this with the non-cached case. We should go through the same code pathway.
                else:
                    logger.info(f"Attempted to use cache on {func_to_track.__qualname__} but it was not cached, or did not exist in the store. Refreshing cache...")
        
        
            _start_time = utc_now()

            # XXX: thread saftey note, if I prevent yielding right here and get the global context I should be fine re: cache key problem

            # get the prompt
            (result, invocation_api_params, metadata) = (
                (func_to_track(*fn_args, **fn_kwargs), {}, {})
                if lmp_type == LMPType.OTHER
                else func_to_track(*fn_args, _invocation_origin=invocation_id, **fn_kwargs, )
                )
            latency_ms = (utc_now() - _start_time).total_seconds() * 1000
            usage = metadata.get("usage", {})
            prompt_tokens=usage.get("prompt_tokens", 0)
            completion_tokens=usage.get("completion_tokens", 0)


            #XXX: cattrs add invocation origin here recursively on all pirmitive types within a message.
            #XXX: This will allow all objects to be traced automatically irrespective origin rather than relying on the API to do it, it will of vourse be expensive but unify track.
            #XXX: No other code will need to consider tracking after this point.

            if not hasattr(func_to_track, "__ell_hash__") and config.lazy_versioning:
                ell.util.closure.lexically_closured_source(func_to_track, forced_dependencies)
            _serialize_lmp(func_to_track)

            if not state_cache_key:
                state_cache_key = compute_state_cache_key(ipstr, func_to_track.__ell_closure__)

            _write_invocation(func_to_track, invocation_id, latency_ms, prompt_tokens, completion_tokens, 
                            state_cache_key, invocation_api_params, cleaned_invocation_params, consumes, result, parent_invocation_id)

            if _get_invocation_id:
                return result, invocation_id
            else:
                return result
        finally:
            pop_invocation()


    func_to_track.__wrapper__  = tracked_func
    if hasattr(func_to_track, "__ell_api_params__"):
        tracked_func.__ell_api_params__ = func_to_track.__ell_api_params__
    if hasattr(func_to_track, "__ell_params_model__"):
        tracked_func.__ell_params_model__ = func_to_track.__ell_params_model__
    tracked_func.__ell_func__ = func_to_track
    tracked_func.__ell_track = True

    return tracked_func

def _serialize_lmp(func):
    # Serialize deptjh first all fo the used lmps.
    for f in func.__ell_uses__:
        _serialize_lmp(f)
    
    if getattr(func, "_has_serialized_lmp", False):
        return
    func._has_serialized_lmp = False
    fn_closure = func.__ell_closure__
    lmp_type = func.__ell_type__
    name = func.__qualname__
    api_params = getattr(func, "__ell_api_params__", None)

    lmps = config.store.get_versions_by_fqn(fqn=name)
    version = 0
    already_in_store = any(lmp.lmp_id == func.__ell_hash__ for lmp in lmps)
    
    if not already_in_store:
        if lmps:
            latest_lmp = max(lmps, key=lambda x: x.created_at)
            version = latest_lmp.version_number + 1
            if config.autocommit:
                from ell.util.differ import write_commit_message_for_diff
                commit = str(write_commit_message_for_diff(
                    f"{latest_lmp.dependencies}\n\n{latest_lmp.source}", 
                    f"{fn_closure[1]}\n\n{fn_closure[0]}")[0])
        else:
            commit = None

        serialized_lmp = SerializedLMP(
            lmp_id=func.__ell_hash__,
            name=name,
            created_at=utc_now(),
            source=fn_closure[0],
            dependencies=fn_closure[1],
            commit_message=commit,
            initial_global_vars=get_immutable_vars(fn_closure[2]),
            initial_free_vars=get_immutable_vars(fn_closure[3]),
            lmp_type=lmp_type,
            api_params=api_params if api_params else None,
            version_number=version,
        )
        config.store.write_lmp(serialized_lmp, [f.__ell_hash__ for f in func.__ell_uses__])
    func._has_serialized_lmp = True

def _write_invocation(func, invocation_id, latency_ms, prompt_tokens, completion_tokens, 
                     state_cache_key, invocation_api_params, cleaned_invocation_params, consumes, result, parent_invocation_id):
    
    invocation_contents = InvocationContents(
        invocation_id=invocation_id,
        params=cleaned_invocation_params,
        results=result,
        invocation_api_params=invocation_api_params,
        global_vars=get_immutable_vars(func.__ell_closure__[2]),
        free_vars=get_immutable_vars(func.__ell_closure__[3])
    )

    if invocation_contents.should_externalize and config.store.has_blob_storage:
        invocation_contents.is_external = True
        
        # Write to the blob store
        blob_id = config.store.blob_store.store_blob(
            invocation_contents.model_dump_json().encode('utf-8'),
            metadata={'invocation_id': invocation_id}
        )
        invocation_contents = InvocationContents(
            invocation_id=invocation_id,
            is_external=True,
        )

    invocation = Invocation(
        id=invocation_id,
        lmp_id=func.__ell_hash__,
        created_at=utc_now(),
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        state_cache_key=state_cache_key,
        used_by_id=parent_invocation_id,
        contents=invocation_contents
    )

    config.store.write_invocation(invocation, consumes)

