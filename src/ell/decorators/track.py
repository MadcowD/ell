import logging
import threading
from ell.types import LMPType, SerializedLStr, utc_now, SerializedLMP, Invocation, InvocationTrace
import ell.util.closure
from ell.configurator import config
from ell.lstr import lstr

import inspect

import cattrs
import numpy as np


import hashlib
import json
import secrets
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Iterable, Optional, OrderedDict, Tuple


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



logger = logging.getLogger(__name__)
def exclude_var(v):
    # is module or is immutable
    return inspect.ismodule(v)

_has_serialized_lmp = {}
_lmp_hash = {}

def track(func_to_track: Callable, *, forced_dependencies: Optional[Dict[str, Any]] = None, lm_kwargs: Optional[Dict[str, Any]] = None, lmp_type: Optional[LMPType] = LMPType.OTHER) -> Callable:

    
    if not ell.util.closure.has_closured_function(func_to_track) and not config.lazy_versioning:
        ell.util.closure.lexically_closured_source(func_to_track, forced_dependencies)

    @wraps(func_to_track)
    def tracked_func(*fn_args, **fn_kwargs) -> str:
        # XXX: Cache keys and global variable binding is not thread safe.
        # Compute the invocation id and hash the inputs for serialization.
        invocation_id = "invocation-" + secrets.token_hex(16)
        state_cache_key : str = None
        if not config._store:
            return func_to_track(*fn_args, **fn_kwargs, _invocation_origin=invocation_id)[0]

        parent_invocation_id = get_current_invocation()
        try:
            push_invocation(invocation_id)
            # Get the list of consumed lmps and clean the invocation paramns for serialization.
            cleaned_invocation_params, ipstr, consumes = prepare_invocation_params(fn_args, fn_kwargs)

            try_use_cache = hasattr(func_to_track.__wrapper__, "__ell_use_cache__")

            if  try_use_cache:
                # Todo: add nice logging if verbose for when using a cahced invocaiton. IN a different color with thar args..
                if not ell.util.closure.has_closured_function(func_to_track) and config.lazy_versioning:
                    fn_closure, _ = ell.util.closure.lexically_closured_source(func_to_track)
                
                # compute the state cachekey
                lexical_closure = ell.util.closure.get_lexical_closure(func_to_track)
                state_cache_key = compute_state_cache_key(ipstr, lexical_closure.closure)
                
                cache_store = func_to_track.__wrapper__.__ell_use_cache__
                cached_invocations = cache_store.get_cached_invocations(lexical_closure.hash, state_cache_key)
                

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
            (result, invocation_kwargs, metadata) = (
                (func_to_track(*fn_args, **fn_kwargs), {}, {})
                if lmp_type == LMPType.OTHER
                else func_to_track(*fn_args, _invocation_origin=invocation_id, **fn_kwargs, )
                )
            latency_ms = (utc_now() - _start_time).total_seconds() * 1000
            usage = metadata.get("usage", {})
            prompt_tokens=usage.get("prompt_tokens", 0)
            completion_tokens=usage.get("completion_tokens", 0)

            if not ell.util.closure.has_closured_function(func_to_track) and config.lazy_versioning:
                ell.util.closure.lexically_closured_source(func_to_track, forced_dependencies)
            _serialize_lmp(func_to_track)

            lexical_closure = ell.util.closure.get_lexical_closure(func_to_track)
            if not state_cache_key:
                state_cache_key = compute_state_cache_key(ipstr, lexical_closure.closure)

            _write_invocation(func_to_track, invocation_id, latency_ms, prompt_tokens, completion_tokens, 
                            state_cache_key, invocation_kwargs, cleaned_invocation_params, consumes, result, parent_invocation_id)

            return result
        finally:
            pop_invocation()


    func_to_track.__wrapper__  = tracked_func
    # XXX: Move away from __ private declarations this should be object oriented.
    if hasattr(func_to_track, "__ell_params_model__"):
        tracked_func.__ell_params_model__ = func_to_track.__ell_params_model__
    tracked_func.__ell_func__ = func_to_track
    tracked_func.__ell_track = True

    return tracked_func

def _serialize_lmp(func):
    # Serialize deptjh first all fo the used lmps.
    lexical_closure = ell.util.closure.get_lexical_closure(func)
    for f in lexical_closure.uses:
        _serialize_lmp(f)
    
    if getattr(func, _has_serialized_lmp[func], False):
        return
    _has_serialized_lmp[func] = True
    fn_closure = func.__ell_closure__
    lmp_type = func.__ell_type__
    name = func.__qualname__
    lm_kwargs = getattr(func, "__ell_lm_kwargs__", None)

    lmps = config._store.get_versions_by_fqn(fqn=name)
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
            lm_kwargs=lm_kwargs if lm_kwargs else None,
            version_number=version,
        )
        config._store.write_lmp(serialized_lmp, [f.__ell_hash__ for f in func.__ell_uses__])
    func._has_serialized_lmp = True

def _write_invocation(func, invocation_id, latency_ms, prompt_tokens, completion_tokens, 
                     state_cache_key, invocation_kwargs, cleaned_invocation_params, consumes, result, parent_invocation_id):
    invocation = Invocation(
        id=invocation_id,
        lmp_id=func.__ell_hash__,
        created_at=utc_now(),
        global_vars=get_immutable_vars(func.__ell_closure__[2]),
        free_vars=get_immutable_vars(func.__ell_closure__[3]),
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        state_cache_key=state_cache_key,
        invocation_kwargs=invocation_kwargs,
        args=cleaned_invocation_params.get('args', []),
        kwargs=cleaned_invocation_params.get('kwargs', {}),
        used_by_id=parent_invocation_id
    )

    results = []
    if isinstance(result, lstr):
        results = [result]
    elif isinstance(result, list):
        results = result
    else:
        raise TypeError("Result must be either lstr or List[lstr]")

    serialized_results = [
        SerializedLStr(
            content=str(res),
            # logits=res.logits
        ) for res in results
    ]

    config._store.write_invocation(invocation, serialized_results, consumes)

def compute_state_cache_key(ipstr, fn_closure):
    _global_free_vars_str = f"{json.dumps(get_immutable_vars(fn_closure[2]), sort_keys=True, default=repr)}"
    _free_vars_str = f"{json.dumps(get_immutable_vars(fn_closure[3]), sort_keys=True, default=repr)}"
    state_cache_key = hashlib.sha256(f"{ipstr}{_global_free_vars_str}{_free_vars_str}".encode('utf-8')).hexdigest()
    return state_cache_key

# TODO: If you are contributo this is a massive place to optimize jesus christ.
# Consider using VS-code's prefered method or gdb's prefered method of strifying symbols recursively.
def get_immutable_vars(vars_dict):
    converter = cattrs.Converter()

    def handle_complex_types(obj):
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [handle_complex_types(item) if not isinstance(item, (int, float, str, bool, type(None))) else item for item in obj]
        elif isinstance(obj, dict):
            return {k: handle_complex_types(v) if not isinstance(v, (int, float, str, bool, type(None))) else v for k, v in obj.items()}
        elif isinstance(obj, (set, frozenset)):
            return list(sorted(handle_complex_types(item) if not isinstance(item, (int, float, str, bool, type(None))) else item for item in obj))
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return f"<Object of type {type(obj).__name__}>"

    converter.register_unstructure_hook(object, handle_complex_types)
    x = converter.unstructure(vars_dict)
    return x

def prepare_invocation_params(fn_args, fn_kwargs):
    invocation_params = dict(
        args=(fn_args),
        kwargs=(fn_kwargs),
    )

    invocation_converter = cattrs.Converter()
    consumes = set()

    def process_lstr(obj):
        consumes.update(obj._origin_trace)
        return invocation_converter.unstructure(dict(content=str(obj), **obj.__dict__, __lstr=True))

    invocation_converter.register_unstructure_hook(
        np.ndarray,
        lambda arr: arr.tolist()
    )
    invocation_converter.register_unstructure_hook(
        lstr,
        process_lstr
    )
    invocation_converter.register_unstructure_hook(
        set,
        lambda s: list(sorted(s))
    )
    invocation_converter.register_unstructure_hook(
        frozenset,
        lambda s: list(sorted(s))
    )
 

    cleaned_invocation_params = invocation_converter.unstructure(invocation_params)
    jstr = json.dumps(cleaned_invocation_params, sort_keys=True, default=repr)
    #  TODO: This is a hack fix it.
    # XXX:  Unify this with above so that we don't have to do this.
    # XXX: I really think there is some standard var explorer we can leverage from from ipython or someshit.
    return json.loads(jstr), jstr, consumes