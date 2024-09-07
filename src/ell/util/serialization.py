
# Global converter
import base64
import hashlib
from io import BytesIO
import json
import cattrs
import numpy as np
from pydantic import BaseModel
import PIL
from ell.types._lstr import _lstr


pydantic_ltype_aware_cattr = cattrs.Converter()

# Register hooks for complex types
pydantic_ltype_aware_cattr.register_unstructure_hook(
    np.ndarray,
    lambda arr: arr.tolist()
)
pydantic_ltype_aware_cattr.register_unstructure_hook(
    set,
    lambda s: list(sorted(s))
)
pydantic_ltype_aware_cattr.register_unstructure_hook(
    frozenset,
    lambda s: list(sorted(s))
)


def serialize_image(img):
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

pydantic_ltype_aware_cattr.register_unstructure_hook(
    PIL.Image.Image,
    lambda obj: {
        "content": serialize_image(obj),
        "__limage": True
    }
)

def unstructure_lstr(obj):
    return dict(content=str(obj), **obj.__dict__, __lstr=True)

pydantic_ltype_aware_cattr.register_unstructure_hook(
    _lstr,
    unstructure_lstr
)

pydantic_ltype_aware_cattr.register_unstructure_hook(
    BaseModel,
    lambda obj: obj.model_dump(exclude_none=True, exclude_unset=True)
)
# Register hooks for complex types (deserialization)


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


def compute_state_cache_key(ipstr, fn_closure):
    _global_free_vars_str = f"{json.dumps(get_immutable_vars(fn_closure[2]), sort_keys=True, default=repr)}"
    _free_vars_str = f"{json.dumps(get_immutable_vars(fn_closure[3]), sort_keys=True, default=repr)}"
    state_cache_key = hashlib.sha256(f"{ipstr}{_global_free_vars_str}{_free_vars_str}".encode('utf-8')).hexdigest()
    return state_cache_key


def prepare_invocation_params(params):
    invocation_params = params

    cleaned_invocation_params = pydantic_ltype_aware_cattr.unstructure(invocation_params)
    
    # Thisis because we wneed the caching to work on the hash of a cleaned and serialized object.
    jstr = json.dumps(cleaned_invocation_params, sort_keys=True, default=repr)

    consumes = set()
    import re
    # XXX: Better than registering a hook in cattrs.
    pattern = r'"__origin_trace__":\s*"frozenset\({(.+?)}\)"'
    
    # Find all matches in the jstr
    matches = re.findall(pattern, jstr)
    
    # Process each match and add to consumes set
    for match in matches:
        # Remove quotes and spaces, then split by comma
        items = [item.strip().strip("'") for item in match.split(',')]
        consumes.update(items)
    consumes = list(consumes)
    # XXX: Only need to reload because of 'input' caching., we could skip this by making ultimate model caching rather than input hash caching; if prompt same use the same output.. irrespective of version.
    return json.loads(jstr), jstr, consumes


def is_immutable_variable(value):
    """
    Check if a value is immutable.

    This function determines whether the given value is of an immutable type in Python.
    Immutable types are objects whose state cannot be modified after they are created.

    Args:
        value: Any Python object to check for immutability.

    Returns:
        bool: True if the value is immutable, False otherwise.

    Note:
        - This function checks for common immutable types in Python.
        - Custom classes are considered mutable unless they explicitly implement
          immutability (which this function doesn't check for).
        - For some types like tuple, immutability is shallow (i.e., the tuple itself
          is immutable, but its contents might not be).
    """
    immutable_types = (
        int, float, complex, str, bytes,
        tuple, frozenset, type(None),
        bool,  # booleans are immutable
        range,  # range objects are immutable
        slice,  # slice objects are immutable
    )

    if isinstance(value, immutable_types):
        return True

    # Check for immutable instances of mutable types
    if isinstance(value, (tuple, frozenset)):
        return all(is_immutable_variable(item) for item in value)

    return False