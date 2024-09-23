# providers/openrouter.py
import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from enum import Enum
from pathlib import Path
from tempfile import gettempdir
from typing import Dict, Any, List, Optional, Union, Tuple, Type

import httpx
from pydantic import BaseModel, Field, field_validator, ValidationError

from ell.configurator import register_provider
from ell.provider import APICallResult, Provider
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
from ell.types.message import LMP
from ell.util.serialization import serialize_image

logger = logging.getLogger(__name__)


class ProviderPreferences(BaseModel):
    """
    Class representing provider preferences for OpenRouter API requests.

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
        # Suggestion: Use GitHub Actions to update this list daily and store it locally in a cache file, and on a CDN.
        # Schema documentation: https://openrouter.ai/docs/provider-routing

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

    @classmethod
    @field_validator('data_collection', 'order', 'ignore', 'quantizations', mode='before')
    def validate_string_or_enum(cls, v):
        if isinstance(v, Enum):
            return v.value
        elif isinstance(v, str):
            return v
        raise ValueError(f"Invalid value: {v}. Expected a string or an enum value.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ProviderPreferences to a dictionary, excluding None values.
        """
        return {k: v for k, v in self.model_dump().items() if v is not None}


class OpenRouter:

    API_VERSION = "v1"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    REQUEST_TIMEOUT = 600

    MODEL_CACHE_DIR = Path(gettempdir()) / "ell_openrouter_cache"
    MODEL_CACHE_FILE = MODEL_CACHE_DIR / "openrouter_models_cache.json"
    MODEL_FILE_CACHE_EXPIRY = 3600  # 60 minutes
    MODEL_CACHE_EXPIRY = 300  # 5 minutes

    def __init__(
            self,
            api_key: Optional[str] = None,
            base_url: str = OPENROUTER_BASE_URL,
            timeout: float = REQUEST_TIMEOUT,
            max_retries: int = 2,
            fetch_generation_data: bool = False,
            provider_preferences: Optional[ProviderPreferences] = None,
    ) -> None:

        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY must be provided or set as an environment variable")

        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.fetch_generation_data = fetch_generation_data

        self.session = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        self.async_session = None

        self._provider_preferences = provider_preferences or ProviderPreferences()

        self._models: Optional[Dict[str, Any]] = None
        self._models_last_fetched: float = 0
        self._used_models: Dict[str, Dict[str, Any]] = {}

        self.global_stats = {
            'total_cost': 0,
            'total_tokens': 0,
            'used_providers': set()
        }

    @property
    def default_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": f"{os.environ.get('HTTP_REFERER', 'http://localhost')}",
            "X-Title": f"{os.environ.get('X_TITLE', 'OpenRouter Python Client')}"
        }

    def _make_request(self, method: str, path: str, delay: float = 1.0, max_attempts: int = 2, timeout: float = None, **kwargs) -> Dict[str, Any]:
        """
        Make a synchronous HTTP request with retries and exponential backoff.
        Supports configurable timeouts and handles both HTTP errors and timeouts.
        """
        url = f"{self.base_url}/{path}"
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

    async def _make_request_async(self, method: str, path: str, delay: float = 1.0, max_attempts: int = 2, timeout: float = None, **kwargs) -> Dict[str, Any]:
        """
        Make an asynchronous HTTP request with retries and exponential backoff.
        Supports configurable timeouts and handles both HTTP errors and timeouts.
        """
        url = f"{self.base_url}/{path}"
        headers = {**self.default_headers, **kwargs.get('headers', {})}

        if not self._initiate_async_session_if_enabled():
            logger.error("Failed to initialize the async session, cannot proceed with the request.")
            return {"error": "Async session not initialized."}

        request_timeout = timeout or self.timeout

        async with self.async_session as async_session:
            for attempt in range(max_attempts):
                try:
                    response = await async_session.request(method, url, headers=headers, timeout=request_timeout, **kwargs)
                    response.raise_for_status()
                    return response.json()

                except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                    logger.warning(f"Async request failed (attempt {attempt + 1}/{max_attempts}): {e}")
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))

    def _initiate_async_session_if_enabled(self, raise_on_error=True) -> bool:
        """Initialize an asynchronous HTTP client session if not already set up.

        Parameters:
            raise_on_error (bool): Whether to raise an error if the session cannot be initialized.

        Returns:
            bool: True if the session was successfully initialized or False if it was not due to absence of an async loop.
        """
        try:
            # Attempt to get the current running event loop
            _ = asyncio.get_running_loop()
            if self.async_session is None:
                self.async_session = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
            return True
        except RuntimeError:
            # No asynchronous running loop available in the current context
            # This typically occurs if the function is called outside of an async context
            return False
        except Exception as e:
            logger.error(f"An error occurred while initializing the async session: {e}")
            if raise_on_error:
                raise RuntimeError("Asynchronous session is not initialized. Ensure that it is set up correctly.")
            return False

    def chat_completions(
            self,
            model: str,
            messages: List[Dict[str, str]],
            temperature: float = 1.0,
            top_p: float = 1.0,
            top_k: int = 0,
            frequency_penalty: float = 0.0,
            presence_penalty: float = 0.0,
            repetition_penalty: float = 1.0,
            min_p: float = 0.0,
            top_a: float = 0.0,
            seed: Optional[int] = None,
            max_tokens: Optional[int] = None,
            logit_bias: Optional[Dict[int, float]] = None,
            logprobs: Optional[bool] = None,
            top_logprobs: Optional[int] = None,
            response_format: Optional[Dict[str, str]] = None,
            stop: Optional[List[str]] = None,
            tools: Optional[List[Dict[str, Any]]] = None,
            tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
            stream: bool = False,
            provider_preferences: Optional['ProviderPreferences'] = None,
            **kwargs: Any
    ) -> Dict[str, Any]:

        json_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "repetition_penalty": repetition_penalty,
            "min_p": min_p,
            "top_a": top_a,
            "seed": seed,
            "max_tokens": max_tokens,
            "logit_bias": logit_bias,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
            "response_format": response_format,
            "stop": stop,
            "tools": tools,
            "tool_choice": tool_choice,
            "stream": stream,
        }

        # Add provider preferences to the request
        if provider_preferences is None:
            provider_preferences = self._provider_preferences
        else:
            provider_preferences = self._process_provider_preferences(provider_preferences)

        if isinstance(provider_preferences, ProviderPreferences):
            json_data["provider"] = provider_preferences.to_dict()

        json_data = {k: v for k, v in json_data.items() if v is not None}
        response = self._make_request("POST", "chat/completions", json=json_data, **kwargs)
        return response

    def get_generation_data(self, generation_id: str, delay: float = 1.0, max_attempts: int = 2) -> Dict[str, Any]:
        return self._make_request("GET", f"generation?id={generation_id}", delay=delay, max_attempts=max_attempts)

    async def get_generation_data_async(self, generation_id: str, delay: float = 1.0, max_attempts: int = 2) -> Dict[str, Any]:
        return await self._make_request_async("GET", f"generation?id={generation_id}", delay=delay, max_attempts=max_attempts)

    def get_parameters(self, model_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"parameters/{model_id}")

    def set_generation_data_preference(self, fetch: bool) -> None:
        """Set the preference for fetching generation data."""
        self.fetch_generation_data = fetch

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

    @property
    def models(self) -> Dict[str, Any]:
        current_time = time.time()
        if self._models is None or (current_time - self._models_last_fetched) > OpenRouter.MODEL_CACHE_EXPIRY:
            self._models = self._fetch_models()
            self._models_last_fetched = current_time
        return self._models

    def _fetch_models(self) -> Dict[str, Any]:
        cached_models = self._get_cached_models()
        if cached_models:
            return cached_models

        models_data = self._make_request("GET", "models")
        models_dictionary = self._transform_models_data(models_data)
        self._save_models_to_cache(models_dictionary)
        return models_dictionary

    @staticmethod
    def _transform_models_data(models_data: Dict[str, Any]) -> Dict[str, Any]:
        models_dictionary = {}
        for model in models_data.get('data', []):
            model_id = model['id']
            models_dictionary[model_id] = model
        return models_dictionary

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

    @property
    def used_models(self) -> Dict[str, Dict[str, Any]]:
        return self._used_models

    @used_models.setter
    def used_models(self, value: Dict[str, Dict[str, Any]]):
        if not isinstance(value, dict):
            raise ValueError("used_models must be a dictionary")
        self._used_models = value

    def clear_model_cache(self):
        self._models = None
        self._models_last_fetched = 0


def get_client(api_key=None, **client_kwargs) -> OpenRouter:
    if api_key is None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set")
    return OpenRouter(api_key=api_key, **client_kwargs)


try:
    class OpenRouterProvider(Provider):
        @staticmethod
        def content_block_to_openrouter_format(content_block: ContentBlock) -> Optional[Dict[str, Any]]:
            if content_block.image:
                if isinstance(content_block.image, str) and content_block.image.startswith(('http://', 'https://', 'data:')):
                    image_url = {"url": content_block.image}
                else:
                    base64_image = serialize_image(content_block.image)
                    image_url = {"url": base64_image}
                if content_block.image_detail:
                    image_url["detail"] = content_block.image_detail
                return {
                    "type": "image_url",
                    "image_url": image_url
                }
            elif content_block.text:
                return {
                    "type": "text",
                    "text": content_block.text
                }
            elif content_block.parsed:
                return {
                    "type": "text",
                    "text": content_block.parsed.model_dump_json()
                }
            else:
                return None

        @staticmethod
        def message_to_openrouter_format(message: Message) -> Dict[str, Any]:
            openrouter_message = {
                "role": "tool" if message.tool_results else message.role,
                "content": list(filter(None, [
                    OpenRouterProvider.content_block_to_openrouter_format(c) for c in message.content
                ])) or None  # Set to None if empty list
            }

            if message.tool_calls:
                try:
                    openrouter_message["tool_calls"] = [
                        {
                            "id": tool_call.tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_call.tool.__name__,
                                "arguments": json.dumps(tool_call.params.model_dump())
                            }
                        } for tool_call in message.tool_calls
                    ]
                    openrouter_message["content"] = None
                except TypeError as e:
                    raise TypeError(
                        f"Error serializing tool calls: {e}. Ensure all @ell.tool decorated functions are fully typed.") from e

            if message.tool_results:
                if not (tool_result := message.tool_results[0]).tool_call_id:
                    raise ValueError("Tool result missing tool_call_id")

                if len(tool_result.result) != 1 or tool_result.result[0].type != "text":
                    raise ValueError("Tool result should contain exactly one text content block")

                openrouter_message.update({
                    "tool_call_id": tool_result.tool_call_id,
                    "content": tool_result.result[0].text
                })

            return openrouter_message

        @classmethod
        def update_stats(cls, client: 'OpenRouter', response: Dict[str, Any]):
            response["client"] = client

            model_name = response.get("model")
            if model_name:
                if model_name not in client.used_models:
                    client.used_models[model_name] = {
                        "total_cost": 0,
                        "total_tokens": 0,
                        "usage_count": 0,
                    }

                usage = response.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                client.used_models[model_name].update({
                    "last_used": response["created"],
                    "last_message_id": response["id"],
                    "usage": usage,
                    "total_tokens": client.used_models[model_name]["total_tokens"] + tokens,
                    "usage_count": client.used_models[model_name]["usage_count"] + 1,
                })
                client.global_stats['total_tokens'] += tokens

            generation_info = response.get("generation_info", {}).get("data")
            if generation_info and isinstance(generation_info, dict):
                model_name = generation_info.get("model")
                if model_name:
                    cost = generation_info.get("total_cost", 0)
                    tokens_prompt = generation_info.get("tokens_prompt", 0)
                    tokens_completion = generation_info.get("tokens_completion", 0)
                    provider = generation_info.get("provider_name")

                    client.used_models[model_name].update({
                        "provider_name": provider,
                        "quantization": generation_info.get("quantization", "unspecified"),
                        "last_used": generation_info.get("created_at"),
                        "total_cost": client.used_models[model_name]["total_cost"] + cost,
                        "tokens_prompt": tokens_prompt,
                        "tokens_completion": tokens_completion,
                        "native_tokens_prompt": generation_info.get("native_tokens_prompt"),
                        "native_tokens_completion": generation_info.get("native_tokens_completion"),
                    })

                    client.global_stats['total_cost'] += cost
                    if provider:
                        client.global_stats['used_providers'].add(provider)

                # Update last_generation_info in global_stats
                client.global_stats['last_generation_info'] = generation_info

        @classmethod
        def schedule_generation_data_update(cls, client: 'OpenRouter', response: Dict[str, Any], delay: float = 1.0, max_attempts: int = 5):
            """Schedule the generation info update, choosing between sync and async methods."""
            generation_id = response.get('id')
            if not generation_id:
                return

            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(cls._update_generation_info_async(client, response, generation_id, delay, max_attempts))
            except RuntimeError:
                # No running event loop, use synchronous update
                cls._update_generation_info_sync(client, response, generation_id, delay, max_attempts)

        @classmethod
        def _update_generation_info_sync(cls, client: 'OpenRouter', response: Dict[str, Any], generation_id: str, delay: float, max_attempts: int):
            """Synchronously update generation info."""
            # This is a chained API request relying on the first API request propagating on OpenRouter servers.
            time.sleep(0.1)  # Use a small sleep to allow the generation ID to propagate
            try:
                generation_info = client.get_generation_data(generation_id, delay=delay, max_attempts=max_attempts)
                if generation_info:
                    response['generation_info'] = generation_info
                    cls.update_stats(client, response)
            except Exception as e:
                print(f"Failed to update generation info synchronously: {e}")

        @classmethod
        async def _update_generation_info_async(cls, client: 'OpenRouter', response: Dict[str, Any], generation_id: str, delay: float, max_attempts: int):
            """Asynchronously update generation info."""
            # This is a chained API request relying on the first API request propagating on OpenRouter servers.
            await asyncio.sleep(0.1)  # Use a small asyncio.sleep to allow the generation ID to propagate
            try:
                generation_info = await client.get_generation_data_async(generation_id, delay=delay, max_attempts=max_attempts)
                if generation_info:
                    response['generation_info'] = generation_info
                    cls.update_stats(client, response)
            except Exception as e:
                print(f"Failed to update generation info asynchronously: {e}")

        @classmethod
        def call_model(
                cls,
                client: 'OpenRouter',
                model: str,
                messages: List[Message],
                api_params: Dict[str, Any],
                tools: Optional[list[LMP]] = None,
        ) -> APICallResult:

            final_call_params = api_params.copy()
            openrouter_messages = [cls.message_to_openrouter_format(message) for message in messages]

            final_call_params["model"] = model
            final_call_params["messages"] = openrouter_messages

            if tools:
                final_call_params["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.__name__,
                            "description": tool.__doc__,
                            "parameters": tool.__ell_params_model__.model_json_schema(),
                        },
                    }
                    for tool in tools
                ]
                final_call_params["tool_choice"] = "auto"

            # Determine whether to fetch generation data, falling back to client if api_params value is not present
            fetch_generation_data = final_call_params.pop("generation_data", client.fetch_generation_data)

            response = client.chat_completions(**final_call_params)

            # Only schedule generation data update if the preference is set
            if fetch_generation_data:
                cls.schedule_generation_data_update(client, response)

            # Update stats with initial data
            cls.update_stats(client, response)

            return APICallResult(
                response=response,
                actual_streaming=final_call_params.get("stream", False),
                actual_n=final_call_params.get("n", 1),
                final_call_params=final_call_params,
            )

        @classmethod
        def process_response(
                cls,
                call_result: APICallResult,
                _invocation_origin: str,
                logger: Optional[Any] = None,
                tools: Optional[List[LMP]] = None,
        ) -> Tuple[List[Message], Dict[str, Any]]:

            response = call_result.response
            client = response.get('client')

            metadata = {
                "id": response.get("id"),
                "created": response.get("created"),
                "model": response.get("model"),
                "object": response.get("object"),
                "system_fingerprint": response.get("system_fingerprint"),
                "usage": response.get("usage", {}),
                "global_stats": client.global_stats if client else {},
                # Note: generation_info might be empty here, because OpenRouter requires a second API call to fetch it
                "generation_info": response.get("generation_info", {}).get("data", {})
            }

            choices_progress = defaultdict(list)
            is_streaming = call_result.actual_streaming

            if is_streaming:
                for chunk in response:
                    for choice in chunk.get("choices", []):
                        choices_progress[choice["index"]].append(choice)
                        if choice["index"] == 0 and logger:
                            logger(choice.get("delta", {}).get("content", ""))
            else:
                for choice in response.get("choices", []):
                    choices_progress[choice["index"]].append(choice)
                    if choice["index"] == 0 and logger:
                        logger(choice.get("message", {}).get("content", ""))

            tracked_results = []
            for _, choice_data in sorted(choices_progress.items(), key=lambda x: x[0]):
                content = []
                role = "assistant"
                finish_reason = None

                if is_streaming:
                    text_content = ""
                    for chunk in choice_data:
                        delta = chunk.get("delta", {})
                        text_content += delta.get("content", "") or ""
                        if "role" in delta:
                            role = delta["role"]
                        finish_reason = chunk.get("finish_reason")

                        if "tool_calls" in delta:
                            cls._process_tool_calls(delta["tool_calls"], content, tools, _invocation_origin)

                    if text_content:
                        content.append(ContentBlock(text=_lstr(content=text_content, _origin_trace=_invocation_origin)))
                else:
                    choice = choice_data[0]
                    message = choice.get("message", {})
                    role = message.get("role", "assistant")
                    finish_reason = choice.get("finish_reason")

                    if message.get("content"):
                        content.append(
                            ContentBlock(text=_lstr(content=message["content"], _origin_trace=_invocation_origin)))

                    if "tool_calls" in message:
                        cls._process_tool_calls(message["tool_calls"], content, tools, _invocation_origin)

                tracked_results.append(
                    Message(
                        role=role,
                        content=content,
                        metadata={"finish_reason": finish_reason}
                    )
                )

            return tracked_results, metadata

        @staticmethod
        def _process_tool_calls(tool_calls, content, tools, _invocation_origin):
            assert tools is not None, "Tools not provided, yet tool calls in response."
            for tool_call in tool_calls:
                matching_tool = next(
                    (tool for tool in tools if tool.__name__ == tool_call["function"]["name"]),
                    None,
                )
                if matching_tool:
                    params = matching_tool.__ell_params_model__(
                        **json.loads(tool_call["function"]["arguments"])
                    )
                    content.append(
                        ContentBlock(
                            tool_call=ToolCall(
                                tool=matching_tool,
                                tool_call_id=_lstr(
                                    tool_call["id"], _origin_trace=_invocation_origin
                                ),
                                params=params,
                            )
                        )
                    )

        @classmethod
        def supports_streaming(cls) -> bool:
            return True

        @classmethod
        def get_client_type(cls) -> Type['OpenRouter']:
            return OpenRouter

    register_provider(OpenRouterProvider)
except ImportError:
    pass


Client = OpenRouter
