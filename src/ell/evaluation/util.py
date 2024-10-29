from functools import wraps
from ell.evaluation.results import Any, Callable, Datapoint, Dict, List
from ell.configurator import config

from typing import Any, Dict, List, Union

from ell.types.message import LMP

def get_lmp_output(
    data_point: Datapoint,
    lmp: LMP,
    lmp_params: Dict[str, Any],
    required_params: bool,
) -> Union[List[Any], Any]:
    if not required_params:
        return lmp(**lmp_params)

    inp = data_point.get("input", None)
    if isinstance(inp, list):
        return lmp(*inp, **lmp_params)
    elif isinstance(inp, dict):
        return lmp(**inp, **lmp_params)
    elif inp is None:
        return lmp(**lmp_params)
    else:
        raise ValueError(f"Invalid input type: {type(inp)}")


def validate_callable_dict(
    items: Union[Dict[str, Callable], List[Callable]], item_type: str
) -> Dict[str, Callable]:
    if isinstance(items, list):
        items_dict = {}
        for item in items:
            if not callable(item):
                raise ValueError(
                    f"Each {item_type} must be a callable, got {type(item)}"
                )
            if not hasattr(item, "__name__") or item.__name__ == "<lambda>":
                raise ValueError(
                    f"Each {item_type} in a list must have a name (not a lambda)"
                )
            items_dict[item.__name__] = item
        return items_dict
    elif isinstance(items, dict):
        for name, item in items.items():
            if not callable(item):
                raise ValueError(
                    f"{item_type.capitalize()} '{name}' must be a callable, got {type(item)}"
                )
        return items
    else:
        raise ValueError(
            f"{item_type}s must be either a list of callables or a dictionary, got {type(items)}"
        )


def needs_store(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not config.store:
            return
        return f(*args, **kwargs)
    return wrapper