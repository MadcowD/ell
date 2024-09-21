import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Type

from ell.configurator import register_provider
from ell.provider import APICallResult, Provider
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
from ell.types.message import LMP
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
                client: 'OpenRouter',
                model: str,
                messages: List[Message],
                api_params: Dict[str, Any],
                tools: Optional[list[LMP]] = None,
        ) -> APICallResult:
            final_call_params = api_params.copy()
            openrouter_messages = [cls.message_to_openrouter_format(message) for message in messages]

            final_call_params["model"] = model
            final_call_params["messages"] = openrouter_messages

            if tools:
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
                final_call_params["tool_choice"] = "auto"

            response = client.chat_completions(**final_call_params)

            # Fetch additional information from the generation endpoint
            generation_id = response.get('id')
            if generation_id:
                generation_info = client.get_generation(generation_id)
                response['generation_info'] = generation_info

            # Update _used_models and global stats based on the chat completion response
            if response.get("model"):
                model_name = response["model"]
                if model_name not in client._used_models:
                    client._used_models[model_name] = {
                        "total_cost": 0,
                        "total_tokens": 0,
                        "usage_count": 0,
                    }

                usage = response.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                client._used_models[model_name].update({
                    "last_used": response["created"],
                    "usage": usage,
                    "total_tokens": client._used_models[model_name]["total_tokens"] + tokens,
                    "usage_count": client._used_models[model_name]["usage_count"] + 1,
                })
                client.global_stats['total_tokens'] += tokens

            # Update _used_models and global stats based on the generation info
            generation_info = response.get("generation_info", {}).get("data")
            if generation_info and isinstance(generation_info, dict):
                model_name = generation_info.get("model")
                if model_name:
                    cost = generation_info.get("total_cost", 0)
                    tokens_prompt = generation_info.get("tokens_prompt", 0)
                    tokens_completion = generation_info.get("tokens_completion", 0)
                    provider = generation_info.get("provider_name")

                    client._used_models[model_name].update({
                        "provider_name": provider,
                        "quantization": generation_info.get("quantization", "unspecified"),
                        "last_used": generation_info.get("created_at"),
                        "total_cost": client._used_models[model_name]["total_cost"] + cost,
                        "tokens_prompt": tokens_prompt,
                        "tokens_completion": tokens_completion,
                        "native_tokens_prompt": generation_info.get("native_tokens_prompt"),
                        "native_tokens_completion": generation_info.get("native_tokens_completion"),
                    })

                    client.global_stats['total_cost'] += cost
                    if provider:
                        client.global_stats['used_providers'].add(provider)

            return APICallResult(
                response=response,
                actual_streaming=final_call_params.get("stream", False),
                actual_n=final_call_params.get("n", 1),
                final_call_params=final_call_params,
            )

        @classmethod
        def process_response(
                cls,
                call_result: APICallResult,
                _invocation_origin: str,
                logger: Optional[Any] = None,
                tools: Optional[List[LMP]] = None,
        ) -> Tuple[List[Message], Dict[str, Any]]:
            response = call_result.response
            metadata = {
                "id": response.get("id"),
                "created": response.get("created"),
                "model": response.get("model"),
                "object": response.get("object"),
                "system_fingerprint": response.get("system_fingerprint"),
                "usage": response.get("usage", {}),
                "generation_info": response.get("generation_info", {}).get("data", {})
            }

            choices_progress = defaultdict(list)
            is_streaming = call_result.actual_streaming

            if is_streaming:
                for chunk in response:
                    for choice in chunk.get("choices", []):
                        choices_progress[choice["index"]].append(choice)
                        if choice["index"] == 0 and logger:
                            logger(choice.get("delta", {}).get("content", ""))
            else:
                for choice in response.get("choices", []):
                    choices_progress[choice["index"]].append(choice)
                    if choice["index"] == 0 and logger:
                        logger(choice.get("message", {}).get("content", ""))

            tracked_results = []
            for _, choice_data in sorted(choices_progress.items(), key=lambda x: x[0]):
                content = []
                role = "assistant"
                finish_reason = None

                if is_streaming:
                    text_content = ""
                    for chunk in choice_data:
                        delta = chunk.get("delta", {})
                        text_content += delta.get("content", "") or ""
                        if "role" in delta:
                            role = delta["role"]
                        finish_reason = chunk.get("finish_reason")

                        if "tool_calls" in delta:
                            cls._process_tool_calls(delta["tool_calls"], content, tools, _invocation_origin)

                    if text_content:
                        content.append(ContentBlock(text=_lstr(content=text_content, _origin_trace=_invocation_origin)))
                else:
                    choice = choice_data[0]
                    message = choice.get("message", {})
                    role = message.get("role", "assistant")
                    finish_reason = choice.get("finish_reason")

                    if message.get("content"):
                        content.append(
                            ContentBlock(text=_lstr(content=message["content"], _origin_trace=_invocation_origin)))

                    if "tool_calls" in message:
                        cls._process_tool_calls(message["tool_calls"], content, tools, _invocation_origin)

                tracked_results.append(
                    Message(
                        role=role,
                        content=content,
                        metadata={"finish_reason": finish_reason}
                    )
                )

            return tracked_results, metadata

        @staticmethod
        def _process_tool_calls(tool_calls, content, tools, _invocation_origin):
            assert tools is not None, "Tools not provided, yet tool calls in response."
            for tool_call in tool_calls:
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

        @classmethod
        def supports_streaming(cls) -> bool:
            return True

        @classmethod
        def get_client_type(cls) -> Type:
            return OpenRouter

    register_provider(OpenRouterProvider)
except ImportError:
    pass