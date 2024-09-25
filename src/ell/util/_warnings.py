from typing import Any, Optional
from colorama import Fore, Style

from ell.configurator import config
import logging
logger = logging.getLogger(__name__)


def _no_api_key_warning(model, client_to_use : Optional[Any], name = None,  long=False, error=False):
    color = Fore.RED if error else Fore.LIGHTYELLOW_EX
    prefix = "ERROR" if error else "WARNING"
    # openai default
    client_to_use_name = client_to_use.__class__.__name__ if (client_to_use) else "OpenAI"
    client_to_use_module = client_to_use.__class__.__module__ if (client_to_use) else "openai"
    lmp_name = f"used by LMP `{name}` " if name else ""
    return f"""{color}{prefix}: No API key found for model `{model}` {lmp_name}using client `{client_to_use_name}`""" + (f""".

To fix this:
* Set your API key in the appropriate environment variable for your chosen provider
* Or, specify a client explicitly in the decorator:
    ```
    import ell
    from {client_to_use_module} import {client_to_use_name}
                                
    @ell.simple(model="{model}", client={client_to_use_name}(api_key=your_api_key))
    def your_lmp_name(...):
        ...
    ```
* Or explicitly specify the client when calling the LMP:

    ```
    your_lmp_name(..., client={client_to_use_name}(api_key=your_api_key))
    ```
""" if long else " at time of definition. Can be okay if custom client specified later! https://docs.ell.so/core_concepts/models_and_api_clients.html ") + f"{Style.RESET_ALL}"


def _warnings(model, fn, default_client_from_decorator):

        if not default_client_from_decorator:
            # Check to see if the model is registered and warn the user we're gonna defualt to OpenAI.

            if model not in config.registry:
                logger.warning(f"""{Fore.LIGHTYELLOW_EX}WARNING: Model `{model}` is used by LMP `{fn.__name__}` but no client could be found that supports `{model}`. Defaulting to use the OpenAI client `{config.default_client}` for `{model}`. This is likely because you've spelled the model name incorrectly or are using a newer model from a provider added after this ell version was released. 
                            
* If this is a mistake either specify a client explicitly in the decorator:
```python
import ell
ell.simple(model, client=my_client)
def {fn.__name__}(...):
    ...
```
or explicitly specify the client when the calling the LMP:

```python
ell.simple(model, client=my_client)(...)
```
{Style.RESET_ALL}""")
            elif (client_to_use := config.registry[model].default_client) is None or not client_to_use.api_key:
                logger.warning(_no_api_key_warning(model, fn.__name__, client_to_use, long=False))


def _autocommit_warning():
    if (config.get_client_for("gpt-4o-mini")[0] is None):
        logger.warning(f"{Fore.LIGHTYELLOW_EX}WARNING: Autocommit is enabled but no OpenAI client found for autocommit model 'gpt-4o-mini' (set your OpenAI API key). Commit messages will not be written.{Style.RESET_ALL}")
        return True
    return False

