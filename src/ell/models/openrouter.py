# src/ell/models/openrouter.py
from __future__ import annotations

from os import makedirs

from ell.configurator import config
import logging
import os
import json
import time
import requests
from typing import List, Dict, Optional

import os
from typing import Any, Union, Mapping
from typing_extensions import Self, override

import httpx

from openai import resources
from openai._qs import Querystring
from openai._types import (
    NOT_GIVEN,
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
)
from openai._utils import (
    is_given,
    is_mapping,
    get_async_library,
)
from openai._version import __version__
from openai._streaming import Stream as Stream, AsyncStream as AsyncStream
from openai._exceptions import OpenAIError, APIStatusError
from openai._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CACHE_FILE = ".pycache/openrouter_models_cache.json"
CACHE_EXPIRY = 3600  # 1 hour


class OpenRouter(SyncAPIClient):
    completions: resources.Completions
    chat: resources.Chat
    embeddings: resources.Embeddings
    models: resources.Models
    with_raw_response: OpenRouterWithRawResponse
    with_streaming_response: OpenRouterWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.Client | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        if api_key is None:
            api_key = os.environ.get("OPENROUTER_API_KEY")
        if api_key is None:
            raise OpenAIError(
                "The api_key client option must be set either by passing api_key to the client or by setting the OPENROUTER_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("OPENROUTER_BASE_URL")
        if base_url is None:
            base_url = "https://openrouter.ai/api/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self._default_stream_cls = Stream

        self.completions = resources.Completions(self)
        self.chat = resources.Chat(self)
        self.embeddings = resources.Embeddings(self)
        self.models = resources.Models(self)
        self.with_raw_response = OpenRouterWithRawResponse(self)
        self.with_streaming_response = OpenRouterWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="brackets")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "HTTP-Referer": os.environ.get("OPENROUTER_REFERRER", ""),
            "X-Title": os.environ.get("OPENROUTER_TITLE", ""),
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        # Implement OpenRouter-specific error handling here
        # For now, we'll use the OpenAI error handling as a placeholder
        return super()._make_status_error(err_msg, body=body, response=response)

class OpenRouterWithRawResponse:
    def __init__(self, client: OpenRouter) -> None:
        self.completions = resources.CompletionsWithRawResponse(client.completions)
        self.chat = resources.ChatWithRawResponse(client.chat)
        self.embeddings = resources.EmbeddingsWithRawResponse(client.embeddings)
        self.models = resources.ModelsWithRawResponse(client.models)

class OpenRouterWithStreamedResponse:
    def __init__(self, client: OpenRouter) -> None:
        self.completions = resources.CompletionsWithStreamingResponse(client.completions)
        self.chat = resources.ChatWithStreamingResponse(client.chat)
        self.embeddings = resources.EmbeddingsWithStreamingResponse(client.embeddings)
        self.models = resources.ModelsWithStreamingResponse(client.models)

try:

    _openrouter_client = None  # Global variable to store the OpenRouter client


    class OpenRouterModel:
        def __init__(self, model_data: Dict):
            self._id = model_data["id"]
            self.id = f'openrouter/{self._id}'

            self.name = model_data["name"]
            self.created = model_data["created"]
            self.description = model_data["description"]
            self.context_length = model_data["context_length"]
            self.architecture = model_data["architecture"]
            self.pricing = model_data["pricing"]
            self.top_provider = model_data["top_provider"]
            self.per_request_limits = model_data["per_request_limits"]

        def __str__(self):
            return f"OpenRouterModel((id={self._id}, name={self.name})"


    def get_cached_models() -> Optional[List[Dict]]:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
            if time.time() - cache_data["timestamp"] < CACHE_EXPIRY:
                return cache_data["models"]
        return None


    def save_models_to_cache(models: List[Dict]):
        cache_data = {
            "timestamp": time.time(),
            "models": models
        }
        makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f)


    def fetch_openrouter_models(api_key: str) -> List[OpenRouterModel]:
        cached_models = get_cached_models()
        if cached_models:
            return [OpenRouterModel(model_data) for model_data in cached_models]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(f"{OPENROUTER_BASE_URL}/models", headers=headers)
        response.raise_for_status()

        models_data = response.json()["data"]
        save_models_to_cache(models_data)

        return [OpenRouterModel(model_data) for model_data in models_data]


    def register(client: OpenRouter):
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")

        try:
            models = fetch_openrouter_models(api_key)
            for model in models:
                config.register_model(model.id, "openrouter")
            logger.info(f"Registered {len(models)} OpenRouter models successfully.")
        except Exception as e:
            logger.error(f"Failed to fetch and register OpenRouter models: {e}")


    def get_openrouter_client() -> OpenRouter:
        global _openrouter_client
        if _openrouter_client is not None:
            return _openrouter_client

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")

        _openrouter_client = OpenRouter(api_key=api_key)
        register(_openrouter_client)
        return _openrouter_client


    try:
        default_client = get_openrouter_client()
        logger.info("Default OpenRouter client created and models registered successfully.")
    except Exception as e:
        logger.warning(f"Failed to create default OpenRouter client: {e}")

except ImportError:
    logger.warning("OpenRouter package not found. OpenRouter models will not be available.")


    def get_openrouter_client():
        raise ImportError("OpenRouter package is not installed. Unable to create OpenRouter client.")