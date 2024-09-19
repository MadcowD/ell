from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple, Type, TypedDict, Union
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

class EllCall(TypedDict):
    messages: List[Message]
    client: Optional[Any] = None
    tools: Optional[List[LMP]] = None
    response_format: Optional[Dict[str, Any]] = None

e = EllCall(messages=[], client=None, tools=None, response_format=None)


class Metadata(TypedDict):
    """First class metadata so that ell studio can work, you can add more stuff here if you want"""
    

class Provider(ABC):
    """
    Abstract base class for all providers. Providers are API interfaces to language models, not necessarily API providers.
    For example, the OpenAI provider is an API interface to OpenAI's API but also to Ollama and Azure OpenAI.
    In Ell. We hate abstractions. The only reason this exists is to force implementers to implement their own provider correctly -_-.
    """

    ################################
    ### API PARAMETERS #############
    ################################
    @abstractmethod
    def provider_call_function(self, **ell_call : EllCall) -> Dict[str, Any]:
        """
        Implement this method to return the function that makes the API call to the language model.
        For example, if you're implementing the OpenAI provider, you would return the function that makes the API call to OpenAI's API.
        ```python
        return openai.Completion.create
        ```
        """
        return NotImplemented
        
    @abstractmethod
    def disallowed_provider_params(self) -> FrozenSet[str]:
        """
        Returns a list of disallowed call params that ell will override.
        """
        return frozenset({"system", "tools", "tool_choice", "stream", "functions", "function_call", "response_format"})

    def available_params(self) -> APICallParams:
        return get_params_of_call_function + EllCall.__required_keys__


    ################################
    ### TRANSLATION ###############
    ################################
    @abstractmethod
    def translate_to_provider(self, ell_call : EllCall) -> APICallParams:
        """Converts an ell call to provider call params!"""
        return NotImplemented
    
    @abstractmethod
    def translate_from_provider(self, provider_response : Any, ell_call : EllCall) -> Tuple[List[Message], Metadata]:
        """Converts provider responses to universal format."""
        return NotImplemented

    ################################
    ### CALL MODEL ################
    ################################
    def call_model(self, client : Optional[Any] = None, model : Optional[str] = None, messages : Optional[List[Message]] = None, tools : Optional[List[LMP]] = None, **api_params) -> Any:
        # Automatic validation of params
        assert api_params.keys() in self.available_params(), f"Invalid parameters: {api_params}"
        assert api_params.keys() not in self.disallowed_provider_params(), f"Disallowed parameters: {api_params}"

        # Call
        call_params = self.translate_to_provider(ell_call)
        provider_resp = self.provider_call_function(client, model)(**call_params)
        return self.translate_from_provider(provider_resp, ell_call)


class Provider2_0(ABC):


    # How do we prevent system param?
    @abstractmethod
    def disallowed_provider_params(self) -> List[str]:
        """
        Returns a list of disallowed call params that ell will override.
        """
        return {"system", "tools", "tool_choice", "stream", "functions", "function_call"}

    
    @abstractmethod
    def translate_provider_to_ell(self, provider_response : Any, ell_call : EllCall) -> Tuple[List[Message], EllMetadata]:
        """Converts provider responses to universal format."""
        return NotImplemented
    
    def call_model(self, client : Optional[Any] = None, model : Optional[str] = None, messages : Optional[List[Message]] = None, tools : Optional[List[LMP]] = None, **api_params) -> Any:
        # Automatic validation of params
        assert api_params.keys() in self.available_params(), f"Invalid parameters: {api_params}"
        assert api_params.keys() not in self.disallowed_provider_params(), f"Disallowed parameters: {api_params}"

        # Call
        call_params = self.translate_ell_to_provider(ell_call)
        provider_resp = self.provider_call_function(client, model)(**call_params)
        return self.translate_provider_to_ell(provider_resp, ell_call)
    