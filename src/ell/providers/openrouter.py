import json
import logging
import os
import time
from enum import Enum
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Dict, List, Optional, Tuple, Union, Iterable

import httpx
from pydantic import BaseModel, Field, ValidationError

from ell.configurator import register_provider
from ell.provider import EllCallParams, Metadata
from ell.types import Message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProviderPreferences(BaseModel):
    """
    Class representing provider preferences for OpenRouter API requests.

    Schema documentation: https://openrouter.ai/docs/provider-routing

    Attributes:
        allow_fallbacks (Optional[bool]): Allow fallback to backup providers if the primary is unavailable.
        require_parameters (Optional[bool]): Ensure that only providers that support all given parameters are selected.
        data_collection (Optional[Union[str, DataCollectionPolicy]]): Specify data collection policy.
        order (Optional[List[Union[str, ProviderName]]]): Ordered list of provider names to attempt.
        ignore (Optional[List[Union[str, ProviderName]]]): List of provider names to ignore.
        quantizations (Optional[List[Union[str, QuantizationLevel]]]): List of quantization levels to filter providers by.
    """

    def __init__(
            self,
            allow_fallbacks: Optional[bool] = True,
            require_parameters: Optional[bool] = False,
            data_collection: Optional[Union['DataCollectionPolicy', str]] = None,
            order: Optional[List[Union['ProviderName', str]]] = None,
            ignore: Optional[List[Union['ProviderName', str]]] = None,
            quantizations: Optional[List[Union['QuantizationLevel', str]]] = None
    ):
        """
        Custom __init__ method to provide explicit parameter hints and manage default mutable types.

        Although Pydantic auto-generates the __init__ method, this custom version makes the expected
        arguments and defaults clearer.
        """
        # Pass to the parent __init__ for Pydantic validation
        super().__init__(
            allow_fallbacks=allow_fallbacks,
            require_parameters=require_parameters,
            data_collection=data_collection,
            order=order,
            ignore=ignore,
            quantizations=quantizations
        )

    class ProviderName(str, Enum):
        """
        Enum for provider names.
        """
        OPENAI = "OpenAI"
        ANTHROPIC = "Anthropic"
        HUGGINGFACE = "HuggingFace"
        TOGETHER = "Together"
        DEEPINFRA = "DeepInfra"
        AZURE = "Azure"
        MODAL = "Modal"
        ANYSCALE = "AnyScale"
        REPLICATE = "Replicate"
        PERPLEXITY = "Perplexity"
        RECURSAL = "Recursal"
        FIREWORKS = "Fireworks"
        MISTRAL = "Mistral"
        GROQ = "Groq"
        COHERE = "Cohere"
        LEPTON = "Lepton"
        OCTOAI = "OctoAI"
        NOVITA = "Novita"
        DEEPSEEK = "DeepSeek"
        INFERMATIC = "Infermatic"
        AI21 = "AI21"
        FEATHERLESS = "Featherless"
        LAMBDA = "Lambda"
        AVIAN = "Avian"
        ZERO_ONE_AI = "01.AI"
        GOOGLE = "Google"
        GOOGLE_AI_STUDIO = "Google AI Studio"
        MANCER = "Mancer"
        MANCER_2 = "Mancer 2"
        HYPERBOLIC = "Hyperbolic"
        HYPERBOLIC_2 = "Hyperbolic 2"
        LYNN_2 = "Lynn 2"
        LYNN = "Lynn"
        REFLECTION = "Reflection"
        # Additional providers can be added as needed.
        # Using ProviderPreferences enums is optional; raw strings or other formats are also supported.
        # Suggestion: Automate updates to this list using GitHub Actions, and store on a CDN and fetch for local caching.
        # For schema details, refer to: https://openrouter.ai/docs/provider-routing

    class QuantizationLevel(str, Enum):
        """
        Enum for quantization levels.
        """
        INT4 = "int4"
        INT8 = "int8"
        FP8 = "fp8"
        FP16 = "fp16"
        BF16 = "bf16"
        UNKNOWN = "unknown"

    class DataCollectionPolicy(str, Enum):
        """
        Enum for data collection policies.
        """
        DENY = "deny"
        ALLOW = "allow"

    allow_fallbacks: Optional[bool] = Field(
        None,
        description="Whether to allow backup providers to serve requests. "
                    "True (default): when the primary provider (or your custom providers in \"order\") is unavailable, use the next best provider. "
                    "False: use only the primary/custom provider, and return the upstream error if it's unavailable."
    )
    require_parameters: Optional[bool] = Field(
        None,
        description="Whether to filter providers to only those that support the parameters you've provided. "
                    "If this setting is omitted or set to false, then providers will receive only the parameters they support, and ignore the rest."
    )
    data_collection: Optional[Union[DataCollectionPolicy, str]] = Field(
        None,
        description="Data collection setting. If no available model provider meets the requirement, your request will return an error. "
                    "Allow (default): allow providers which store user data non-transiently and may train on it. "
                    "Deny: use only providers which do not collect user data."
    )
    order: Optional[List[Union[ProviderName, str]]] = Field(
        None,
        description="An ordered list of provider names. The router will attempt to use the first provider in the subset of this list that supports your requested model, "
                    "and fall back to the next if it is unavailable. If no providers are available, the request will fail with an error message."
    )
    ignore: Optional[List[Union[ProviderName, str]]] = Field(
        None,
        description="List of provider names to ignore. If provided, this list is merged with your account-wide ignored provider settings for this request."
    )
    quantizations: Optional[List[Union[QuantizationLevel, str]]] = Field(
        None,
        description="A list of quantization levels to filter the provider by."
    )

    class Config:
        use_enum_values = True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ProviderPreferences to a dictionary, excluding None values.
        """
        return {k: v for k, v in self.model_dump().items() if v is not None}


try:
    from ell.providers.openai import OpenAIProvider
    import openai

    class OpenRouter(openai.Client):

        OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

        REQUEST_TIMEOUT = 600

        MODEL_CACHE_DIR = Path(gettempdir()) / "ell_cache"
        MODEL_CACHE_FILE = MODEL_CACHE_DIR / "openrouter_models_cache.json"
        MODEL_FILE_CACHE_EXPIRY = 3600  # 60 minutes
        MODEL_CACHE_EXPIRY = 300  # 5 minutes

        def __init__(self, api_key: Optional[str] = None, base_url: str = OPENROUTER_BASE_URL,
                     timeout: float = REQUEST_TIMEOUT, max_retries: int = 2,
                     provider_preferences: Optional[ProviderPreferences] = None) -> None:
            """Construct a new synchronous OpenRouter client instance, a subclass of a synchronous openai client instance.
            This automatically infers the `api_key` from the `OPENROUTER_API_KEY` environment variable if it is not provided.
            """
            if api_key is None:
                api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError(
                    "The api_key client option must be set either by passing api_key to the client or by setting the OPENROUTER_API_KEY environment variable"
                )
            super().__init__(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=max_retries)

            self.base_url = base_url
            self.timeout = timeout
            self.session = httpx.Client(base_url=self.base_url, timeout=self.timeout)

            self._provider_preferences = provider_preferences or ProviderPreferences()
            self._models: Optional[Dict[str, Any]] = None
            self._models_last_fetched: float = 0
            self._used_models: Dict[str, Dict[str, Any]] = {}

            self.global_stats = {
                'total_cost': 0.,
                'total_tokens': 0,
                'used_providers': set()
            }

        @property
        def default_headers(self) -> Dict[str, str]:
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

        def get_model_parameters(self, model_id: str, *args, **kwargs) -> Dict[str, Any]:
            response_json =  self._make_request("GET", f"parameters/{model_id}", *args, **kwargs)
            return response_json.get("data", {})

        def get_generation_data(self, generation_id: str, *args, **kwargs) -> Dict[str, Any]:
            response_json = self._make_request("GET", f"generation?id={generation_id}", *args, **kwargs)
            return response_json.get("data", {})

        @property
        def provider_preferences(self) -> Optional[ProviderPreferences]:
            return self._provider_preferences

        @provider_preferences.setter
        def provider_preferences(self, value: Optional[Union[Dict, ProviderPreferences]]):
            if value is None:
                value = ProviderPreferences()
            self._provider_preferences = self._process_provider_preferences(value)

        def set_provider_preferences(self, preferences: Union[Dict, ProviderPreferences]) -> None:
            """Set the provider preferences."""
            self._provider_preferences = self._process_provider_preferences(preferences)

        def clear_provider_preferences(self) -> None:
            """Clear the provider preferences."""
            self._provider_preferences = ProviderPreferences()

        @classmethod
        def _process_provider_preferences(cls, preferences: Optional[Union[Dict, ProviderPreferences]]) -> Optional[ProviderPreferences]:
            if preferences is None:
                return None
            if isinstance(preferences, ProviderPreferences):
                return preferences
            if isinstance(preferences, dict):
                try:
                    return ProviderPreferences(**preferences)
                except ValidationError as e:
                    logger.warning(f"OpenRouter Client: Invalid provider preferences: {e}")
                    return None
            raise ValueError("provider_preferences must be either a dictionary or an instance of ProviderPreferences")

        def get_models(self, model_ids: Union[str, Iterable[str], None] = None) -> Dict[str, Any]:
            """Retrieve model(s) from cache or API, returning a dict of specified model ids or all models."""
            current_time = time.time()
            if self._models is None or (current_time - self._models_last_fetched) > self.MODEL_CACHE_EXPIRY:
                cached_models = self._get_cached_models()

                if not cached_models:
                    models_list = self.models.list()
                    if not hasattr(models_list, 'data'):
                        raise ValueError("Unexpected data format received from models.list()")

                    models_dictionary = {model.id: model.to_dict() for model in models_list.data}
                    if not models_dictionary:
                        raise ValueError("No models found in the response")

                    self._save_models_to_cache(models_dictionary)
                else:
                    models_dictionary = cached_models

                self._models = models_dictionary
                self._models_last_fetched = current_time

            if model_ids is None:
                return self._models
            if isinstance(model_ids, str):
                return {model_ids: self._models.get(model_ids)} if model_ids in self._models else {}
            if isinstance(model_ids, Iterable):
                return {model: self._models[model] for model in model_ids if model in self._models}
            raise ValueError("Invalid input type. Expected str, Iterable[str], or None.")

        @property
        def used_models(self) -> Dict[str, Dict[str, Any]]:
            return self._used_models

        @used_models.setter
        def used_models(self, value: Dict[str, Dict[str, Any]]):
            if not isinstance(value, dict):
                raise ValueError("used_models must be a dictionary")
            self._used_models = value

        def clear_used_models(self) -> None:
            self._used_models = {}

        def clear_model_cache(self):
            self._models = None
            self._models_last_fetched = 0
            if os.path.exists(OpenRouter.MODEL_CACHE_FILE):
                os.remove(OpenRouter.MODEL_CACHE_FILE)

        @staticmethod
        def _get_cached_models() -> Optional[Dict[str, Any]]:
            if OpenRouter.MODEL_CACHE_FILE.exists():
                with OpenRouter.MODEL_CACHE_FILE.open("r") as f:
                    cache_data = json.load(f)
                if time.time() - cache_data["timestamp"] < OpenRouter.MODEL_FILE_CACHE_EXPIRY:
                    return cache_data["models"]
            return None

        @staticmethod
        def _save_models_to_cache(models: Dict[str, Any]):
            cache_data = {
                "timestamp": time.time(),
                "models": models
            }
            OpenRouter.MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with OpenRouter.MODEL_CACHE_FILE.open("w") as f:
                json.dump(cache_data, f)

        def _make_request(
                self,
                method: str,
                path: str,
                delay: float = 1.0,
                max_attempts: int = 2,
                timeout: float = None,
                **kwargs
        ) -> Dict[str, Any]:
            """
            Make a synchronous HTTP request with retries and exponential backoff.
            Supports configurable timeouts and handles both HTTP errors and timeouts.
            """
            url = f"{self.base_url}{path}"
            headers = {**self.default_headers, **kwargs.get('headers', {})}
            request_timeout = timeout or self.timeout

            for attempt in range(max_attempts):
                try:
                    response = self.session.request(method, url, headers=headers, timeout=request_timeout, **kwargs)
                    response.raise_for_status()
                    return response.json()

                except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_attempts}): {e}")
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))


    def get_client(api_key=None, **client_kwargs) -> OpenRouter:
        return OpenRouter(api_key=api_key, **client_kwargs)


    class OpenRouterProvider(OpenAIProvider):
        def translate_to_provider(self, ell_call: EllCallParams):
            # OpenRouter-specific intrinsics
            provider_preferences = ell_call.api_params.pop('provider_preferences', None)

            params = super().translate_to_provider(ell_call)
            params.pop('stream_options', None)

            # OpenRouter-specific intrinsics, if any, can be added here.
            openrouter_client = ell_call.client
            if provider_preferences is None:
                provider_preferences = openrouter_client.provider_preferences
            if isinstance(provider_preferences, ProviderPreferences):
                params["extra_body"] = {"provider": provider_preferences.to_dict()}
            elif isinstance(provider_preferences, dict):
                params["extra_body"] = {"provider": provider_preferences}
            return params

        def translate_from_provider(self, *args, **kwargs) -> Tuple[List[Message], Metadata]:
            messages, metadata = super().translate_from_provider(*args, **kwargs)
            ell_call = next((arg for arg in args if isinstance(arg, EllCallParams)), None)
            if ell_call is not None and hasattr(ell_call, "client"):
                openrouter_client = ell_call.client
                self.update_stats(openrouter_client, metadata)
                metadata["global_stats"] = openrouter_client.global_stats
            else:
                raise ValueError("Invalid arguments: Expected EllCallParams with a client attribute")
            return messages, metadata

        @classmethod
        def update_stats(cls, client: 'OpenRouter', metadata: Dict[str, Any]):
            """Update usage statistics and cost estimates based on the provided metadata."""
            model_name = metadata.get("model")
            provider = metadata.get("provider")
            usage = metadata.get("usage", {})

            if model_name:
                # Retrieve model information
                model_info = next(iter(client.get_models(model_name).values()), {})
                pricing = model_info.get('pricing', {})

                model_stats = client.used_models.setdefault(model_name, {
                    "total_tokens": 0.,
                    "usage_count": 0.,
                    "total_cost": 0.,
                })

                total_tokens = usage.get("total_tokens", 0)
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

                # Calculate cost
                prompt_cost = float(pricing.get('prompt', 0.)) * prompt_tokens
                completion_cost = float(pricing.get('completion', 0.)) * completion_tokens
                total_cost = prompt_cost + completion_cost

                model_stats.update({
                    "last_used": metadata["created"],
                    "last_message_id": metadata["id"],
                    "provider_name": provider,
                    "total_tokens": model_stats["total_tokens"] + total_tokens,
                    "usage_count": model_stats["usage_count"] + 1,
                    "last_usage": usage,
                    "total_cost": model_stats["total_cost"] + total_cost,
                    "tokens_prompt": model_stats.get("tokens_prompt", 0) + prompt_tokens,
                    "tokens_completion": model_stats.get("tokens_completion", 0) + completion_tokens,
                })

                # Update global stats
                client.global_stats['total_tokens'] = client.global_stats.get('total_tokens', 0) + total_tokens
                client.global_stats['total_cost'] = client.global_stats.get('total_cost', 0.) + total_cost
                if provider:
                    client.global_stats.setdefault('used_providers', set()).add(provider)

            # Update last_metadata in global_stats
            client.global_stats['last_metadata'] = metadata

    # Register the provider and set alias for Client
    register_provider(OpenRouterProvider(), OpenRouter)
    Client = OpenRouter
except ImportError:
    pass
