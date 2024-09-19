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
     model : str
     messages : List[Message]
     client : Any
     tools : Optional[List[LMP]]
     response_format : Optional[Dict[str, Any]]

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
    def provider_call_function(self) -> Dict[str, Any]:
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

    def available_params(self) -> Partial[APICallParams]:
        return frozenset(get_params_of_call_function(provider_call_params.keys())) + EllCall.__required_keys__ - disallowed_params


    ################################
    ### TRANSLATION ###############
    ################################
    @abstractmethod
    def translate_to_provider(self, ) -> APICallParams:
        """Converts an ell call to provider call params!"""
        return NotImplemented
    
    @abstractmethod
    def translate_from_provider(self, provider_response : Any, ell_call : EllCall) -> Tuple[List[Message], Metadata]:
        """Converts provider responses to universal format."""
        return NotImplemented

    ################################
    ### CALL MODEL ################
    ################################
    def call_model(self, model : Optional[str] = None, client : Optional[Any] = None, messages : Optional[List[Message]] = None, tools : Optional[List[LMP]] = None, **api_params) -> Any:
        # Automatic validation of params

        assert api_params.keys() not in self.disallowed_provider_params(), f"Disallowed parameters: {api_params}"
        assert api_params.keys() in self.available_params(), f"Invalid parameters: {api_params}"

        # Call
        call_params = self.translate_to_provider(ell_call)
        provider_resp = self.provider_call_function(client, model)(**call_params)
        return self.translate_from_provider(provider_resp, ell_call)

    def default_models(self) -> List[str]:
        """Returns a list of default models for this provider."""
        return [
        ]
    
    def register_all_models(self, client : Any):
        """Registers all default models for this provider."""
        for model in self.default_models():
            self.register_model(model, client)

    def validate_call(self, call : EllCall):
         if model == "o1-preview" or model == "o1-mini":
                # Ensure no system messages are present
                assert all(msg['role'] != 'system' for msg in final_call_params['messages']), "System messages are not allowed for o1-preview or o1-mini models"
                                      
        if self.model_is_available(call.model):
            return
        else:
            raise ValueError(f"Model {call.model} not available for provider {self.name}")
        

class OpenAIClientProvider(Provider):
     """Use this for providers that are a wrapper around an OpenAI client e.g. mistral, groq, azure, etc."""

     ...

class OpenAIProvider(OpenAIClientProvider):
    def default_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-05-13",
            "gpt-4o-2024-07-18",
            "gpt-4o-2024-06-20",
            "gpt-4o-2024-04-09",
            "gpt-4o-2024-03-13",
            "gpt-4o-2024-02-29",
        ]
    
    def validate_call(self, call : EllCall):
         super().validate_call(call)
         if model == "o1-preview" or model == "o1-mini":
                # Ensure no system messages are present
                assert all(msg['role'] != 'system' for msg in final_call_params['messages']), "System messages are not allowed for o1-preview or o1-mini models"
    
    def provider_call_function(self, EllCall) -> Dict[str, Any]: 
        if EllCall['response_format']:
            return EllCall['client'].beta.chat.completions.parse(**EllCall)
        else:
            return EllCall['client'].chat.completions.create(**EllCall)
        
    def available_params(self, ell_call : EllCall) -> Partial[APICallParams]:
        defualt_params = get_params_of_call_function(self.provider_call_function(ell_call))

        if ell_call['response_format']: 
             # no streaming currently
             eturn defualt_params - {'stream'}
        else:
            return defualt_params

class OllamaProvider(OpenAIClientProvider):
    def default_models(self) -> List[str]:
        





