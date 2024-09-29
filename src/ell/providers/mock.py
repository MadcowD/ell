import random
import string

from typing import Optional, Dict, Any, List, Type, Tuple
from ell.provider import Provider, EllCallParams, Metadata
from ell.types import Message
from ell.types.message import LMP
from ell.configurator import config, register_provider
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast


class MockAIClient:

    def __init__(self, **kwargs):
        self.api_key = "mock"

    def chat_completions_create(self, **kwargs):
        return None


class MockAIProvider(Provider):
    dangerous_disable_validation = True

    def provider_call_function(
        self, client: MockAIClient, api_call_params: Optional[Dict[str, Any]] = None
    ) -> Callable[..., Any]:
        return client.chat_completions_create

    def translate_to_provider(self, ell_call: EllCallParams) -> Dict[str, Any]:
        return ell_call.api_params.copy()

    def default_mock_func(self) -> Tuple[List[Message], Metadata]:
        results = []
        random_str = "".join(
            random.choices(
                string.ascii_letters + string.digits, k=random.randint(1, 40)
            )
        )
        results.append(
            Message(
                role=("user"),
                content="mock_" + random_str,
            )
        )
        return results, Metadata

    def translate_from_provider(
        self,
        _provider_response: Any,
        _ell_call: EllCallParams,
        provider_call_params: Dict[str, Any],
        _origin_id: Optional[str] = None,
        _logger: Optional[Callable[..., None]] = None,
    ) -> Tuple[List[Message], Metadata]:
        if "mock_func" in provider_call_params:
            mock_func = provider_call_params["mock_func"]
            return [Message(role=("user"), content=mock_func())], Metadata
        else:
            return self.default_mock_func()


register_provider(MockAIProvider(), MockAIClient)
