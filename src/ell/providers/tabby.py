from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from ell.provider import APICallResult, Provider
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
import json
from ell.configurator import config, register_provider
from ell.types.message import LMP
from ell.util.serialization import serialize_image

try: 
    import openai
    class TabbyProvider(Provider):
        def message_to_simple_openai_format(message: Message) -> List[Dict[str, Any]]:         
            formatted_message = []
            for content in message.content:
                if content.text:  # Check if the content text is not empty
                    formatted_message = {
                        "role": message.role,
                        "content": content.text
                    }
            return formatted_message
            

        @classmethod
        def call_model(
            cls,
            client: Any,
            model: str,
            messages: List[Message],
            api_params: Dict[str, Any],
            tools: Optional[list[LMP]] = None,
        ) -> APICallResult:
            final_call_params = api_params.copy()
            openai_messages = [cls.message_to_simple_openai_format(message) for message in messages]

            actual_n = api_params.get("n", 1)
            final_call_params["model"] = model
            final_call_params["messages"] = openai_messages

            response = client.chat.completions.create(**final_call_params)
            final_call_params.pop("stream", None)
            final_call_params.pop("stream_options", None)

            return APICallResult(
                response=response,
                actual_streaming=isinstance(response, openai.Stream),
                actual_n=actual_n,
                final_call_params=final_call_params,
            )

        @classmethod
        def process_response(
            cls, call_result: APICallResult, _invocation_origin: str, logger: Optional[Any] = None, tools: Optional[List[LMP]] = None,
        ) -> Tuple[List[Message], Dict[str, Any]]:
            choices_progress = defaultdict(list)
            api_params = call_result.final_call_params
            metadata = {}

            if hasattr(call_result.response, "choices"):
                for chunk in call_result.response.choices:
                    if hasattr(chunk, "usage") and chunk.usage:
                        metadata = chunk.to_dict()

                    choices_progress[chunk.index].append(chunk)
            else:
                # Handle the case when the response is a single message
                choice = call_result.response
                if choice.content:
                    choices_progress[0].append(choice)

            tracked_results = []
            for _, choice_deltas in sorted(choices_progress.items(), key=lambda x: x[0]):
                content = []

                choice = choice_deltas[0].message
                if choice.content:
                    content.append(
                        ContentBlock(
                            text=_lstr(
                                content=choice.content, _origin_trace=_invocation_origin
                            )
                        )
                    )

                tracked_results.append(
                    Message(
                        role=choice.role,
                        content=content,
                    )
                )
            return tracked_results, metadata


        @classmethod
        def supports_streaming(cls) -> bool:
            return True

        @classmethod
        def get_client_type(cls) -> Type:
            return openai.Client



    register_provider(TabbyProvider)
except ImportError:
    pass