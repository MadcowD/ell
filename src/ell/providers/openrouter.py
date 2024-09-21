from typing import Any, Dict, List, Optional, Tuple, Type
from collections import defaultdict
import json
from ell.provider import APICallResult, Provider
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
from ell.types.message import LMP
from ell.configurator import register_provider
from ell.util.serialization import serialize_image

try:
    from ell.models.openrouter import OpenRouter

    class OpenRouterProvider(Provider):
        @staticmethod
        def content_block_to_openrouter_format(content_block: ContentBlock) -> Optional[Dict[str, Any]]:
            if content_block.image:
                base64_image = serialize_image(content_block.image)
                image_url = {"url": base64_image}
                if content_block.image_detail:
                    image_url["detail"] = content_block.image_detail
                return {
                    "type": "image_url",
                    "image_url": image_url
                }
            elif content_block.text:
                return {
                    "type": "text",
                    "text": content_block.text
                }
            elif content_block.parsed:
                return {
                    "type": "text",
                    "text": content_block.parsed.model_dump_json()
                }
            else:
                return None

        @staticmethod
        def message_to_openrouter_format(message: Message) -> Dict[str, Any]:
            openrouter_message = {
                "role": "tool" if message.tool_results else message.role,
                "content": list(filter(None, [
                    OpenRouterProvider.content_block_to_openrouter_format(c) for c in message.content
                ]))
            }
            if message.tool_calls:
                openrouter_message["tool_calls"] = [
                    {
                        "id": tool_call.tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call.tool.__name__,
                            "arguments": json.dumps(tool_call.params.model_dump())
                        }
                    } for tool_call in message.tool_calls
                ]
                openrouter_message["content"] = None

            if message.tool_results:
                openrouter_message["tool_call_id"] = message.tool_results[0].tool_call_id
                openrouter_message["content"] = message.tool_results[0].result[0].text
            return openrouter_message

        @classmethod
        def call_model(
            cls,
            client: OpenRouter,
            model: str,
            messages: List[Message],
            api_params: Dict[str, Any],
            tools: Optional[list[LMP]] = None,
        ) -> APICallResult:
            final_call_params = api_params.copy()
            openrouter_messages = [cls.message_to_openrouter_format(message) for message in messages]

            actual_n = api_params.get("n", 1)
            final_call_params["model"] = model
            final_call_params["messages"] = openrouter_messages

            if tools:
                final_call_params["tool_choice"] = "auto"
                final_call_params["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.__name__,
                            "description": tool.__doc__,
                            "parameters": tool.__ell_params_model__.model_json_schema(),
                        },
                    }
                    for tool in tools
                ]

            response = client.chat_completions(**final_call_params)

            generation_id = response.get('id')
            if generation_id:
                generation_info = client.get_generation(generation_id)
                response['generation_info'] = generation_info

            return APICallResult(
                response=response,
                actual_streaming=final_call_params.get("stream", False),
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

            if not call_result.actual_streaming:
                response = [call_result.response]
            else:
                response = call_result.response

            for chunk in response:
                if "usage" in chunk:
                    metadata["usage"] = chunk["usage"]

                for choice in chunk.get("choices", []):
                    choices_progress[choice["index"]].append(choice)

                    if choice["index"] == 0 and logger:
                        logger(choice.get("delta", {}).get("content", "") if call_result.actual_streaming else
                               choice.get("message", {}).get("content", ""))

            tracked_results = []
            for _, choice_deltas in sorted(choices_progress.items(), key=lambda x: x[0]):
                content = []

                if call_result.actual_streaming:
                    text_content = "".join(
                        (choice.get("delta", {}).get("content", "") or "" for choice in choice_deltas)
                    )
                    if text_content:
                        content.append(
                            ContentBlock(
                                text=_lstr(
                                    content=text_content, _origin_trace=_invocation_origin
                                )
                            )
                        )
                    streamed_role = next((choice.get("delta", {}).get("role") for choice in choice_deltas if choice.get("delta", {}).get("role")), 'assistant')
                else:
                    choice = choice_deltas[0].get("message", {})
                    if choice.get("content"):
                        content.append(
                            ContentBlock(
                                text=_lstr(
                                    content=choice["content"], _origin_trace=_invocation_origin
                                )
                            )
                        )

                if not call_result.actual_streaming and "tool_calls" in choice:
                    assert tools is not None, "Tools not provided, yet tool calls in response."
                    for tool_call in choice["tool_calls"]:
                        matching_tool = next(
                            (tool for tool in tools if tool.__name__ == tool_call["function"]["name"]),
                            None,
                        )
                        if matching_tool:
                            params = matching_tool.__ell_params_model__(
                                **json.loads(tool_call["function"]["arguments"])
                            )
                            content.append(
                                ContentBlock(
                                    tool_call=ToolCall(
                                        tool=matching_tool,
                                        tool_call_id=_lstr(
                                            tool_call["id"], _origin_trace=_invocation_origin
                                        ),
                                        params=params,
                                    )
                                )
                            )

                tracked_results.append(
                    Message(
                        role=(
                            choice.get("message", {}).get("role")
                            if not call_result.actual_streaming
                            else streamed_role
                        ),
                        content=content,
                    )
                )
            return tracked_results, metadata

        @classmethod
        def supports_streaming(cls) -> bool:
            return True

        @classmethod
        def get_client_type(cls) -> Type:
            return OpenRouter

    register_provider(OpenRouterProvider)
except ImportError:
    pass