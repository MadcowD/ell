from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
import json
from dataclasses import dataclass
from ell.types.message import LMP


@dataclass
class APICallResult:
    response: Any
    actual_streaming: bool
    actual_n: int
    final_call_params: Dict[str, Any]


class Provider(ABC):
    """
    Abstract base class for all providers. Providers are API interfaces to language models, not necessarily API providers.
    For example, the OpenAI provider is an API interface to OpenAI's API but also to Ollama and Azure OpenAI.
    """

    @classmethod
    @abstractmethod
    def call_model(
        cls,
        client: Any,
        model: str,
        messages: List[Any],
        api_params: Dict[str, Any],
        tools: Optional[list[LMP]] = None,
    ) -> APICallResult:
        """Make the API call to the language model and return the result along with actual streaming, n values, and final call parameters."""
        pass

    @classmethod
    @abstractmethod
    def process_response(
        cls, call_result: APICallResult, _invocation_origin: str, logger: Optional[Any] = None, tools: Optional[List[LMP]] = None,
    ) -> Tuple[List[Message], Dict[str, Any]]:
        """Process the API response and convert it to ell format."""
        pass

    @classmethod
    @abstractmethod
    def supports_streaming(cls) -> bool:
        """Check if the provider supports streaming."""
        pass

    @classmethod
    @abstractmethod
    def get_client_type(cls) -> Type:
        """Return the type of client this provider supports."""
        pass
