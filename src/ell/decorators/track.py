import ell.util.closure
from ell.configurator import config
from ell.lstr import lstr


import cattrs
import numpy as np


import hashlib
import json
import secrets
import time
from datetime import datetime
from functools import wraps
from typing import Callable


def track(fn: Callable) -> Callable:
    if hasattr(fn, "__ell_lm_kwargs__"):
        func_to_track = fn
        lm_kwargs = fn.__ell_lm_kwargs__
        lmp = True
    else:
        func_to_track = fn
        lm_kwargs = None
        lmp = False


    # see if it exists
    _name = func_to_track.__qualname__
    _has_serialized_lmp = False
    _has_computed_lexical_closure_this_runtime = False


    @wraps(fn)
    def wrapper(*fn_args, **fn_kwargs) -> str:
        nonlocal _has_serialized_lmp
        if not config._store:
            return fn(*fn_args, **fn_kwargs)[0]

        # Compute the invocation id and hash the inputs for serialization.
        invocation_id = "invocation-" + secrets.token_hex(16)
        # Get the list of consumed lmps and clean the invocation paramns for serialization.
        cleaned_invocation_params, input_hash, consumes = prepare_invocation_params(fn_args, fn_kwargs)
    
        if hasattr(wrapper, "__ell_use_cache__"):
            if wrapper.__ell_use_cache__:
                cache_key = input_hash
                # cached_invocation = store().get_cached_invocation(fn_hash, input_hash)
                # return [d.deserialzie() for  d in cached_invocatiopn.result]
                return NotImplemented

        if False and fn.__ell_use_cache__:
            cache_key = input_hash
            # cached_invocation = store().get_cached_invocation(fn_hash, input_hash)
            # return [d.deserialzie() for  d in cached_invocatiopn.result]
            return NotImplemented
        else:
            _start_time = datetime.now()
            # get the prompt
            (result, invocation_kwargs, metadata) = (
                (fn(*fn_args, **fn_kwargs), None)
                if not lmp
                else fn(*fn_args, _invocation_origin=invocation_id, **fn_kwargs, )
                )
            latency_ms = (datetime.now() - _start_time).total_seconds() * 1000
            usage = metadata.get("usage", {})
            prompt_tokens=usage.get("prompt_tokens", 0)
            completion_tokens=usage.get("completion_tokens", 0)


            if not _has_serialized_lmp:
                fn_closure, _uses = ell.util.closure.lexically_closured_source(func_to_track)

                # Compute commit messages if enabled
                commit = None
                lmps = config._store.get_lmps(name=_name)
                version = 0
                already_in_store =any(lmp['lmp_id'] == func_to_track.__ell_hash__ for lmp in lmps)
                if not already_in_store:
                    # Do auto commitng and versioning if previous versions exist.
                    if len(lmps) > 0 :
                        lmps.sort(key=lambda x: x['created_at'], reverse=True)
                        latest_lmp = lmps[0]


                        version = (latest_lmp['version_number']) + 1
                        print(latest_lmp['version_number'], version)
                        if config.autocommit:
                        # Get the latest lmp
                        # sort by created at  
                            from ell.util.differ import write_commit_message_for_diff
                            commit = str(write_commit_message_for_diff(f"{latest_lmp['dependencies']}\n\n{latest_lmp['source']}", f"{fn_closure[1]}\n\n{fn_closure[0]}")[0])


                    config._store.write_lmp(
                        lmp_id=func_to_track.__ell_hash__,
                        name=_name,
                        created_at=datetime.now(),
                        source=fn_closure[0],
                        dependencies=fn_closure[1],
                        commit_message=(commit),
                        is_lmp=lmp,
                        lm_kwargs=(
                            (lm_kwargs)
                            if lm_kwargs
                            else None
                        ),
                        version_number=version,
                        uses=_uses,
                    )
                    _has_serialized_lmp = True

                config._store.write_invocation(id=invocation_id,
                    lmp_id=func_to_track.__ell_hash__,  created_at=datetime.now(),
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    input_hash=input_hash,
                    invocation_kwargs=invocation_kwargs,
                    **cleaned_invocation_params, consumes=consumes, result=result)

            return result

    fn.__wrapper__  = wrapper
    wrapper.__ell_lm_kwargs__ = lm_kwargs
    wrapper.__ell_func__ = func_to_track
    wrapper.__ell_track = True

    return wrapper



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
    input_hash = hashlib.sha256(json.dumps(cleaned_invocation_params, sort_keys=True).encode('utf-8')).hexdigest()
    return cleaned_invocation_params, input_hash, consumes

