from colorama import Fore, Style

from ell.configurator import config
import logging
logger = logging.getLogger(__name__)


def _no_api_key_warning(model, name, client_to_use, long=False, error=False):
    color = Fore.RED if error else Fore.LIGHTYELLOW_EX
    prefix = "ERROR" if error else "WARNING"
    return f"""{color}{prefix}: No API key found for model `{model}` used by LMP `{name}` using client `{client_to_use}`""" + (""".

To fix this:
* Or, set your API key in the environment variable `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,  etc.
* Or, specify a client explicitly in the decorator:
    ```
    import ell
    import openai
                                
    ell.lm(model, client=openai.Client(api_key=my_key))
    def {name}(...):
        ...
    ```
* Or explicitly specify the client when the calling the LMP:

    ```
    ell.lm(model, client=openai.Client(api_key=my_key))(...)
    ```
""" if long else " at time of definition. Can be okay if custom client specified later! <TODO: add link to docs> ") + f"{Style.RESET_ALL}"


def _warnings(model, fn, default_client_from_decorator):

        if not default_client_from_decorator:
            # Check to see if the model is registered and warn the user we're gonna defualt to OpenAI.

            if model not in config.registry:
                logger.warning(f"""{Fore.LIGHTYELLOW_EX}WARNING: Model `{model}` is used by LMP `{fn.__name__}` but no client could be found that supports `{model}`. Defaulting to use the OpenAI client `{config.default_client}` for `{model}`. This is likely because you've spelled the model name incorrectly or are using a newer model from a provider added after this ell version was released. 
                            
* If this is a mistake either specify a client explicitly in the decorator:
```python
import ell
ell.lm(model, client=my_client)
def {fn.__name__}(...):
    ...
```
or explicitly specify the client when the calling the LMP:

```python
ell.lm(model, client=my_client)(...)
```
{Style.RESET_ALL}""")
            elif (client_to_use := config.registry[model]) is None or not client_to_use.api_key:
                logger.warning(_no_api_key_warning(model, fn.__name__, client_to_use or '', long=False))