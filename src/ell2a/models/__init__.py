"""
Attempts to registeres model names with their respective API client bindings. This allows for the creation of a unified interface for interacting with different LLM providers.

For example, to register an OpenAI model:
@ell2a.simple(model='gpt-4o-mini') -> @ell2a.simple(model='gpt-4o-mini', client=openai.OpenAI())

"""

import ell2a.models.openai
import ell2a.models.anthropic
import ell2a.models.ollama
import ell2a.models.groq
import ell2a.models.bedrock
