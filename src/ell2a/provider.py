from abc import ABC, abstractmethod
from collections import defaultdict
from functools  import lru_cache
import inspect
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypedDict,
    Union,
)

from pydantic import BaseModel, ConfigDict, Field
from ell2a.types import Message, ContentBlock, AgentCall
from ell2a.types._lstr import _lstr
import json
from dataclasses import dataclass
from ell2a.types.message import LMP


# XXX: Might leave this internal to providers so that the complex code is simpler &
# we can literally jsut call provider.call like any openai fn.
class Ell2aCallParams(BaseModel):
    model: str = Field(..., description="Model identifier")
    messages: List[Message] = Field(..., description="Conversation context")
    client: Any = Field(..., description="API client")
    agents: List[LMP] = Field(default_factory=list,
                             description="Available agents")
    api_params: Dict[str, Any] = Field(
        default_factory=dict, description="API parameters"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_agent_by_name(self, name: str) -> Optional[LMP]:
        """Get a agent by name."""
        return next(
            (agent for agent in (self.agents or []) if agent.__name__ == name), None
        )


Metadata = Dict[str, Any]

# XXX: Needs a better name.


class Provider(ABC):
    """
    Abstract base class for all providers. Providers are API interfaces to language models, not necessarily API providers.
    For example, the OpenAI provider is an API interface to OpenAI's API but also to Ollama and Azure OpenAI.
    In Ell2a. We hate abstractions. The only reason this exists is to force implementers to implement their own provider correctly -_-.
    """
    dangerous_disable_validation = False

    ################################
    ### API PARAMETERS #############
    ################################
    @abstractmethod
    def provider_call_function(
        self, client: Any, api_call_params: Optional[Dict[str, Any]] = None
    ) -> Callable[..., Any]:
        """
        Implement this method to return the function that makes the API call to the language model.
        For example, if you're implementing the OpenAI provider, you would return the function that makes the API call to OpenAI's API.
        """
        return NotImplemented

    def disallowed_api_params(self) -> FrozenSet[str]:
        """
        Returns a list of disallowed call params that ell2a will override.
        """
        return frozenset({"messages", "agents", "model", "stream", "stream_options"})

    def available_api_params(self, client: Any, api_params: Optional[Dict[str, Any]] = None):
        params = _call_params(self.provider_call_function(client, api_params))
        return frozenset(params.keys()) - self.disallowed_api_params()

    ################################
    ### TRANSLATION ###############
    ################################
    @abstractmethod
    def translate_to_provider(self, ell2a_call: Ell2aCallParams) -> Dict[str, Any]:
        """Converts an ell2a call to provider call params!"""
        return NotImplemented

    @abstractmethod
    def translate_from_provider(
        self,
        provider_response: Any,
        ell2a_call: Ell2aCallParams,
        provider_call_params: Dict[str, Any],
        origin_id: Optional[str] = None,
        logger: Optional[Callable[..., None]] = None,
    ) -> Tuple[List[Message], Metadata]:
        """Converts provider responses to universal format. with metadata"""
        return NotImplemented

    ################################
    ### CALL MODEL ################
    ################################
    # Be careful to override this method in your provider.
    def call(
        self,
        # XXX: In future refactors, we can fully enumerate the args and make ell2a_call's internal to the _provider implementer interface.
        # This gives us a litellm style interface for free.
        ell2a_call: Ell2aCallParams,
        origin_id: Optional[str] = None,
        logger: Optional[Any] = None,
    ) -> Tuple[List[Message], Dict[str, Any], Metadata]:
        # Automatic validation of params
        assert (
            not set(ell2a_call.api_params.keys()).intersection(
                self.disallowed_api_params())
        ), f"Disallowed api parameters: {ell2a_call.api_params}"

        final_api_call_params = self.translate_to_provider(ell2a_call)

        call = self.provider_call_function(
            ell2a_call.client, final_api_call_params)
        assert self.dangerous_disable_validation or _validate_provider_call_params(
            final_api_call_params, call)

        provider_resp = call(**final_api_call_params)

        messages, metadata = self.translate_from_provider(
            provider_resp, ell2a_call, final_api_call_params, origin_id, logger
        )
        assert "choices" not in metadata, "choices should be in the metadata."
        assert self.dangerous_disable_validation or _validate_messages_are_tracked(
            messages, origin_id)

        return messages, final_api_call_params, metadata


# handhold the the implementer, in production mode we can turn these off for speed.
@lru_cache(maxsize=None)
def _call_params(call: Callable[..., Any]) -> MappingProxyType[str, inspect.Parameter]:
    return inspect.signature(call).parameters


def _validate_provider_call_params(
    api_call_params: Dict[str, Any], call: Callable[..., Any]
):
    provider_call_params = _call_params(call)

    required_params = {
        name: param
        for name, param in provider_call_params.items()
        if param.default == param.empty and param.kind != param.VAR_KEYWORD
    }

    for param_name in required_params:
        assert (
            param_name in api_call_params
        ), f"Provider implementation error: Required parameter '{param_name}' is missing in the converted call parameters converted from ell2a call."

    for param_name, param_value in api_call_params.items():
        assert (
            param_name in provider_call_params
        ), f"Provider implementation error: Unexpected parameter '{param_name}' in the converted call parameters."

    return True


def _validate_messages_are_tracked(
    messages: List[Message], origin_id: Optional[str] = None
):
    if origin_id is None:
        return

    for message in messages:
        assert isinstance(
            message.text, _lstr
        ), f"Provider implementation error: Message text should be an instance of _lstr, got {type(message.text)}"
        assert (
            origin_id in message.text.__origin_trace__
        ), f"Provider implementation error: Message origin_id {message.text.__origin_trace__} does not match the provided origin_id {origin_id}"
    return True
