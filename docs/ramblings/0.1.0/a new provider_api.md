
# Goal with this refactor

# - Force a clean provider interface so that implementers build compatible and maintainable interfaces

# - Automate testing of new providers

# - Make the code as understandable as possible

# - Manage all the metadata around providers in one place

# - Providers should specify what they are capable of so we can validate at compile time that it makese sense (what params are available)

def validate_call_params(self, model : str, client : Any, api_params : Dict[str, Any]) -> None:
    """Validates the call parameters."""
    pass

class ProviderCapabilities(BaseModel):
    """The capabilities of a provider. This allowes ell2a to validate at compile time that a provider supports the features it needs."""
    supports_streaming : bool
    supports_structured_outputs : bool
    supports_function_calling : bool
    supports_agent_calling : bool

@abstractmethod
def capabilities(self, model : str, client : Any) -> ProviderCapabilities:
    """Returns the capabilities of the provider."""
    pass

@abstractmethod
def ell2a_call_to_provider_call(self, ell2a_call : Ell2aCall) -> T:
    """Converts an Ell2aCall to a provider call."""
    pass

@abstractmethod
def provider_response_to_ell2a_response(self, ell2a_call : Ell2aCall, provider_response : Any) -> Ell2aResponse:
    """Converts a provider response to an Ell2a response."""
    pass

class Provider(ABC)

    @abstractmethod
    def provider_call_function(self, client) -> Callable:
        """Returns the function that makes the call to the provider."""
        return NotImplemented


class OpenAIProvider(Provider):
    def provider_call_function(self, client) -> Callable:
        return client.chat.completions.create

import inspect
from typing import Any, Dict

def validate_provider_call_params(self, ell2a_call: Ell2aCall, client: Any):
    provider_call_func = self.provider_call_function(client)
    provider_call_params = inspect.signature(provider_call_func).parameters

    converted_params = self.ell2a_call_to_provider_call(ell2a_call)

    required_params = {
        name: param for name, param in provider_call_params.items()
        if param.default == param.empty and param.kind != param.VAR_KEYWORD
    }

    for param_name in required_params:
        assert param_name in converted_params, f"Required parameter '{param_name}' is missing in the converted call parameters."

    for param_name, param_value in converted_params.items():
        assert param_name in provider_call_params, f"Unexpected parameter '{param_name}' in the converted call parameters."

        param_type = provider_call_params[param_name].annotation
        if param_type != inspect.Parameter.empty:
            assert isinstance(param_value, param_type), f"Parameter '{param_name}' should be of type {param_type}."

    print("All parameters validated successfully.")

# How do we force the nick scenario

# If we use response_format -> we sshould parse the resposne into the universal format

# i like that u can use your proviers params in your @ell2a.call

# alterntively we coudl do the vercel shit

# universal params: subset of params

class UniversalParams(BaseModel):
    messages : List[Message]

@ell2a.simple(openai("gpt-4", **openai params), agents=[], ell2a params.. )

# Trying to currently solve hte params problem. I dont want you to have to learn a new set of params. You should be able to use your API params however you want

# Not even a universal set of params. But then we get ugly shit like

@ell2a.simple("claude-3", system="hi")

# Process

# (messages + agents + widgets) -> (call params + messages) -> (resposne (no streaming)) -> (messages + metadata)

#

# is that api params can live inside of messages

# Compoenents aroudn are

# 1. we create the call parameters

# 2. we validate the call parameters

    # Certain things arent allowed like stream=True for non-streaming providers

# 3. we send them to the api

# 4. we translate the response to universal format

# 5. we return the resposne toe hte api file

# Params

# eveyr api has their own set of params. the ell2a way right now is fine, but some should be prohibited and we want to know what params are available

# can solve using

class Provider2_0(ABC):

    """Universal Parameters"""
    @abstractmethod
    def provider_call_function(self, client : Optional[Any] = None, model : Optional[str] = None) -> Dict[str, Any]:
        return NotImplemented

    # How do we prevent system param?
    @abstractmethod
    def disallowed_provider_params(self) -> List[str]:
        """
        Returns a list of disallowed call params that ell2a will override.
        """
        return {"system", "agents", "agent_choice", "stream", "functions", "function_call"}

    def available_params(self):
        return inspect.signature(self.provider_call_function).parameters - self.disallowed_provider_params()

    """Universal Messages"""
    @abstractmethod
    def translate_ell2a_to_provider(self, ell2a_call : Ell2aCall) -> Any:
        """Converts universal messages to the provider-specific format."""
        return NotImplemented

    @abstractmethod
    def translate_provider_to_ell(self, provider_response : Any, ell2a_call : Ell2aCall) -> Tuple[List[Message], Ell2aMetadata]:
        """Converts provider responses to universal format."""
        return NotImplemented

    def call_model(self, client : Optional[Any] = None, model : Optional[str] = None, messages : Optional[List[Message]] = None, agents : Optional[List[LMP]] = None, **api_params) -> Any:
        # Automatic validation of params
        assert api_params.keys() in self.available_params(), f"Invalid parameters: {api_params}"
        assert api_params.keys() not in self.disallowed_provider_params(), f"Disallowed parameters: {api_params}"

        # Call
        call_params = self.translate_ell2a_to_provider(ell2a_call)
        provider_resp = self.provider_call_function(client, model)(**call_params)
        return self.translate_provider_to_ell(provider_resp, ell2a_call)


class CallMetadata(BaseModel):
    """A universal metadata format for ell2a studio?"""
    usage : Optional[Usage] = None
    model : Optional[str] = None
    provider : Optional[str] = None
    provider_response : Optional[Any] = None
    other : Optional[Dict[str, Any]] = None

# TODO: How does this interact with streaming? Cause isn't the full story

# Translationc

# How do we force implementers to implement parameter translation like agents etc

# What about capabilities? Why do we need to know? Well if there aren't any agents available

def translate_provider_to_ell(
    ell2a_call : Ell2aCall,
    provider_response : Any
) -> Tuple[[Message], CallMetadata]:
    """Converts provider responses to universal format."""
    return NotImplemented

# We have to actually test with a known provider response which we cant automatically do

# We could force providers to extract agentcalls from the response and then we wouldnt have to do it for every provider

@ell2a.simple(agents=[myagent], system="hi")
def my_prompt(self, client, model, messages, agents, **api_params):
    return "usethist agent"

# This is bad because we providers have different levels of multimodality etc

class Provider(ABC):

    @abstractmethod
    def response_to_agent_calls(self, provider_response : Any) -> List[AgentCall]:
        """Extracts agent calls from the provider response."""
        return NotImplemented

    @abstractmethod
    def response_to_content(self, provider_response : Any) -> str:
        """Extracts the content from the provider response."""
        return NotImplemented

# How would you guarantee that a provider? Respond with a agent call if a agent call occurs within the provider

# Without actually knowing the details of the provider, there's no way To guarantee this. It almost has to be like A required argument of the response construction

# So you could. Require the implementer to say if there were A agent call or not in the response

# It's not possible to prevent people from writing **** code. Like we can't know if they're stupid provider has a type of a response that's not a agent call

# Unless we really explicitly add them mark what was in the response

# Models (maybe models should live close to providers)

# This prevents us from doing routing but that's actualyl openrouters purpose

# right now we stream by default

# but this a problemn for models dont support it we'd ahve to make two requests which imo is a nono

# Future todo stream=False is default. We don't log steaming completions with verbose mode

# Set verbose_stream=False to stop background streaming, or pass stream=False

register_model(
    name="",
    default_client=client,
    disallowed_params={"stream", "stream_options"},
    default_params={"stream": False, "stream_options": {}},
)

# if you set stream=False we dont log streaming completions
