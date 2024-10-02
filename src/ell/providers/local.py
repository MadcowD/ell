from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
)

from ell.configurator import register_provider
from ell.provider import EllCallParams, Metadata, Provider
from ell.types import ContentBlock, Message
from ell.types._lstr import _lstr

try:
    import gpt4all

    class LocalModelClient(gpt4all.GPT4All):
        # should probably fix the way this is done in _warnings via: `not client_to_use.api_key`
        api_key = "okay"

except ImportError:
    raise ImportError("Please install the gpt4all package to use the LocalProvider.")


class LocalProvider(Provider):
    """
    Custom Provider for LocalProvider models.
    """

    dangerous_disable_validation = True  # Set to True to bypass validation if necessary

    def _construct_prompt(self, messages: list[Message]) -> str:
        """
        Constructs a single prompt string from the list of ell Messages.
        Adjust this method based on how LocalProvider expects the prompt to be formatted.

        Might need this as part of client.chat_session() in provider_call_function.
        """
        prompt = ""
        for message in messages:
            if message.role == "system":
                prompt += f"System: {message.text_only}\n"
            elif message.role == "user":
                prompt += f"User: {message.text_only}\n"
            elif message.role == "assistant":
                prompt += f"Assistant: {message.text_only}\n"
            # Handle other roles if necessary
        return prompt.strip()

    def provider_call_function(
        self,
        client: Any,
        api_call_params: dict[str, Any] = {},
    ) -> Callable[..., Any]:
        """
        Returns the function to call on the client with the given API call parameters
        """
        if api_call_params.get("streaming", False):
            raise NotImplementedError("Streaming responses not yet supported.")

        with client.chat_session():
            # not clear to me if you need to put the system prompt and prompt template in chat_session
            return client.generate

    def translate_to_provider(self, ell_call: EllCallParams) -> dict[str, Any]:
        """
        Translates EllCallParams to LocalProvider's generate method parameters.
        """
        final_call_params = {
            "prompt": self._construct_prompt(ell_call.messages),
            "max_tokens": ell_call.api_params.get("max_tokens", 200),
            "temp": ell_call.api_params.get("temperature", 0.7),
            "top_k": ell_call.api_params.get("top_k", 40),
            "top_p": ell_call.api_params.get("top_p", 0.4),
            "min_p": ell_call.api_params.get("min_p", 0.0),
            "repeat_penalty": ell_call.api_params.get("repeat_penalty", 1.18),
            "repeat_last_n": ell_call.api_params.get("repeat_last_n", 64),
            "n_batch": ell_call.api_params.get("n_batch", 8),
            "n_predict": ell_call.api_params.get("n_predict", None),
            "streaming": ell_call.api_params.get("stream", False),
            # callback of `None` type on gpt4all will cause errors
            # "callback": ell_call.api_params.get("callback", None),
        }

        # Handle tools if any
        if ell_call.tools:
            # LocalProvider might not support tools directly; handle accordingly
            # This is a placeholder for tool integration
            final_call_params["tools"] = [
                {
                    "name": tool.__name__,
                    "description": tool.__doc__,
                    "parameters": tool.__ell_params_model__.model_json_schema(),
                }
                for tool in ell_call.tools
            ]

        return final_call_params

    def translate_from_provider(
        self,
        provider_response: Iterable[str] | str,
        ell_call: EllCallParams,
        provider_call_params: dict[str, Any],
        origin_id: Optional[str] = None,
        logger: Optional[Callable[..., None]] = None,
    ) -> tuple[list[Message], Metadata]:
        """
        Translates LocalProvider's response back into ell's Message and Metadata formats.
        Handles both streaming and non-streaming responses.
        """
        metadata: Metadata = {}
        messages: list[Message] = []
        streaming = provider_call_params.get("streaming", False)

        if streaming and isinstance(provider_response, Iterable):
            # Handle streaming responses
            raise NotImplementedError("Streaming responses not yet supported.")
        else:
            # Handle non-streaming responses
            if isinstance(provider_response, str):
                messages.append(
                    Message(
                        role="assistant",
                        content=[
                            ContentBlock(
                                text=_lstr(
                                    content=provider_response, origin_trace=origin_id
                                )
                            )
                        ],
                    )
                )
            else:
                raise ValueError(
                    "Unexpected provider_response type for non-streaming response."
                )

        return messages, metadata


register_provider(LocalProvider(), LocalModelClient)
