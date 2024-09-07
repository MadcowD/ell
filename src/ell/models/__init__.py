"""
Attempts to registeres model names with their respective API client bindings. This allows for the creation of a unified interface for interacting with different LLM providers.

For example, to register an OpenAI model:
@ell.simple(model='gpt-4o-mini') -> @ell.simple(model='gpt-4o-mini', client=openai.OpenAI())

"""

import ell.models.openai
import ell.models.ollama