from typing import Optional
from ell.configurator import config

try:
    from groq import Groq
    def register(client: Optional[Groq] = None, **client_kwargs):
        if client is None:
            client = Groq(**client_kwargs)
        for model in client.models.list().data:
            config.register_model(model.id, default_client=client, supports_streaming=True)
except ImportError:
    pass