# src/ell/models/openrouter.py
from ell.configurator import config

import json
import logging
import os
import time
from pathlib import Path
from tempfile import gettempdir
from typing import Dict, Any, Optional, Union, Literal, List

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_CACHE_DIR = Path(gettempdir()) / "ell_openrouter_cache"
MODEL_CACHE_FILE = MODEL_CACHE_DIR / "openrouter_models_cache.json"
MODEL_FILE_CACHE_EXPIRY = 3600  # 60 minutes

client = None  # Global: OpenRouter client


class OpenRouter:

    MODEL_CACHE_EXPIRY = 300  # 5 minutes

    def __init__(
            self,
            api_key: Optional[str] = None,
            base_url: str = OPENROUTER_BASE_URL,
            timeout: float = 600,
            max_retries: int = 2,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY must be provided or set as an environment variable")

        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = httpx.Client(base_url=self.base_url, timeout=self.timeout)

        self._models: Optional[Dict[str, Any]] = None
        self._models_last_fetched: float = 0
        self._used_models: Dict[str, Dict[str, Any]] = {}

        self._provider_preferences = None

    @property
    def default_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": f"{os.environ.get('HTTP_REFERER', 'http://localhost')}",
            "X-Title": f"{os.environ.get('X_TITLE', 'OpenRouter Python Client')}"
        }

    def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{path}"
        headers = {**self.default_headers, **kwargs.get('headers', {})}
        # response = self.session.request(method, url, headers=headers, **kwargs)
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

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

        json_data = {k: v for k, v in json_data.items() if v is not None}
        response = self._make_request("POST", "chat/completions", json=json_data, **kwargs)

        # Update used_models
        if 'model' in response:
            model_info = response['model']
            model_id = f"{model_info['name']}/{model_info['provider']}/{model_info.get('quantization', 'full')}"
            self._used_models[model_id] = {
                "supported_parameters": model_info.get('supported_parameters', []),
                "provider": model_info['provider'],
                "quantization": model_info.get('quantization', 'full')
            }

        return response

    def get_parameters(self, model_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"parameters/{model_id}")

    def set_provider_preferences(
            self,
            allow_fallbacks: Optional[bool] = None,
            require_parameters: Optional[bool] = None,
            data_collection: Optional[Literal["deny", "allow"]] = None,
            order: Optional[List[str]] = None,
            ignore: Optional[List[str]] = None,
            quantizations: Optional[List[Literal["int4", "int8", "fp8", "fp16", "bf16", "unknown"]]] = None
    ) -> None:
        self._provider_preferences = {
            "allow_fallbacks": allow_fallbacks,
            "require_parameters": require_parameters,
            "data_collection": data_collection,
            "order": order,
            "ignore": ignore,
            "quantizations": quantizations
        }
        self._provider_preferences = {k: v for k, v in self._provider_preferences.items() if v is not None}

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
        if MODEL_CACHE_FILE.exists():
            with MODEL_CACHE_FILE.open("r") as f:
                cache_data = json.load(f)
            if time.time() - cache_data["timestamp"] < MODEL_FILE_CACHE_EXPIRY:
                return cache_data["models"]
        return None

    @staticmethod
    def _save_models_to_cache(models: Dict[str, Any]):
        cache_data = {
            "timestamp": time.time(),
            "models": models
        }
        MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with MODEL_CACHE_FILE.open("w") as f:
            json.dump(cache_data, f)

    @property
    def used_models(self) -> Dict[str, Dict[str, Any]]:
        return self._used_models

    def clear_model_cache(self):
        self._models = None
        self._models_last_fetched = 0


class OpenRouterModel:
    def __init__(self, model_data: Dict):
        self.id = model_data["id"]
        self.name = model_data["name"]
        self.created = model_data["created"]
        self.description = model_data["description"]
        self.context_length = model_data["context_length"]
        self.architecture = model_data["architecture"]
        self.pricing = model_data["pricing"]
        self.top_provider = model_data["top_provider"]
        self.per_request_limits = model_data["per_request_limits"]

    def __str__(self):
        return f"OpenRouterModel(id={self.id}, name={self.name})"


def fetch_openrouter_models(openrouter_client: OpenRouter) -> List[OpenRouterModel]:
    return [OpenRouterModel(model_data) for model_data in openrouter_client.models.values()]


def register_openrouter_models(openrouter_client: OpenRouter):
    try:
        models = fetch_openrouter_models(openrouter_client)
        for model in models:
            config.register_model(model.id, client)
        logger.info(f"Registered {len(models)} OpenRouter models successfully.")
    except Exception as e:
        logger.error(f"Failed to fetch and register OpenRouter models: {e}")

def get_client(api_key=None) -> OpenRouter:
    global client
    if api_key is None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set")
    if client is None:
        client = OpenRouter(api_key=api_key)
    return client

try:
    client = get_client()
    register_openrouter_models(client)
    logger.info("Default OpenRouter client created and models registered successfully.")
except Exception as e:
    logger.warning(f"Failed to create default OpenRouter client or register models: {e}")

