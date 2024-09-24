"""
Groq provider.
"""

from ell.providers.openai import OpenAIProvider
from ell.configurator import register_provider


try:
    import groq
    class GroqProvider(OpenAIProvider):
        dangerous_disable_validation = True
        def translate_to_provider(self, *args, **kwargs):
            params = super().translate_to_provider(*args, **kwargs)
            params.pop('stream_options', None)
            return params
        
        def translate_from_provider(self, *args, **kwargs):
            res, meta = super().translate_from_provider(*args, **kwargs)
            if not meta['usage']:
                meta['usage'] = meta['x_groq']['usage']
            return res, meta
    register_provider(GroqProvider(), groq.Client)
except ImportError:
    pass

