from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple, Type, TypedDict, Union

from pydantic import BaseModel, ConfigDict, Field
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
import json
from dataclasses import dataclass
from ell.types.message import LMP


class EllCallParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model: str = Field(..., description="Model identifier")
    messages: List[Message] = Field(..., description="Conversation context")
    client: Any = Field(..., description="API client")
    tools: Optional[List[LMP]] = Field(None, description="Available tools")
    api_params: Dict[str, Any] = Field(default_factory=dict, description="API parameters")
    origin_id: Optional[str] = Field(None, description="Tracking ID")


class Metadata(TypedDict):
    """First class metadata so that ell studio can work, you can add more stuff here if you want"""
    
#XXX: Needs a better name.
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
    def provider_call_function(self, api_call_params : Dict[str, Any]) -> Callable[..., Any]:
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
        pass

    def available_params(self) -> APICallParams:
        return frozenset(get_params_of_call_function(provider_call_params.keys())) + EllCallParams.__required_keys__ - disallowed_params


    ################################
    ### TRANSLATION ###############
    ################################
    @abstractmethod
    def translate_to_provider(self, ell_call : EllCallParams) -> Dict[str, Any]:
        """Converts an ell call to provider call params!"""
        return NotImplemented
    
    @abstractmethod
    def translate_from_provider(self, provider_response : Any, ell_call : EllCallParams, logger : Optional[Callable[[str], None]] = None) -> Tuple[List[Message], Metadata]:
        """Converts provider responses to universal format."""
        return NotImplemented

    ################################
    ### CALL MODEL ################
    ################################
    # Be careful to override this method in your provider.
    def call_model(self, ell_call : EllCallParams, logger : Optional[Any] = None) -> Tuple[List[Message], Dict[str, Any], Metadata]:
        # Automatic validation of params

        assert ell_call.api_params.keys() not in self.disallowed_provider_params(), f"Disallowed parameters: {ell_call.api_params}"
        assert ell_call.api_params.keys() in self.available_params(), f"Invalid parameters: {ell_call.api_params}"

        # Call
        api_call_params = self.translate_to_provider(ell_call)
        provider_resp = self.provider_call_function(api_call_params)(**api_call_params)
        messages, metadata = self.translate_from_provider(provider_resp, ell_call, logger)
        
        return messages, api_call_params, metadata


        



# # 
# def validate_provider_call_params(self, ell_call: EllCall, client: Any):
#     provider_call_func = self.provider_call_function(client)
#     provider_call_params = inspect.signature(provider_call_func).parameters
    
#     converted_params = self.ell_call_to_provider_call(ell_call)
    
#     required_params = {
#         name: param for name, param in provider_call_params.items()
#         if param.default == param.empty and param.kind != param.VAR_KEYWORD
#     }
    
#     for param_name in required_params:
#         assert param_name in converted_params, f"Required parameter '{param_name}' is missing in the converted call parameters."
    
#     for param_name, param_value in converted_params.items():
#         assert param_name in provider_call_params, f"Unexpected parameter '{param_name}' in the converted call parameters."
        
#         param_type = provider_call_params[param_name].annotation
#         if param_type != inspect.Parameter.empty:
#             assert isinstance(param_value, param_type), f"Parameter '{param_name}' should be of type {param_type}."
    
#     print("All parameters validated successfully.")



