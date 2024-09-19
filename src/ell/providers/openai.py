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
    class OpenAIProvider(Provider):

        # XXX: This content block conversion etc might need to happen on a per model basis for providers like groq etc. We will think about this at a future date.
        @staticmethod
        def content_block_to_openai_format(content_block: ContentBlock) -> Dict[str, Any]:
            if content_block.image:
                base64_image = serialize_image(content_block.image)
                image_url = {"url": base64_image}

                # add detail only if supplied by user
                # OpenAI's default is "auto", we omit the "detail" key entirely if not provided by user
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
            # Tool calls handled in message_to_openai_format.
            #XXX: Feel free to refactor this.
            else:
                return None

        @staticmethod
        def message_to_openai_format(message: Message) -> Dict[str, Any]:
            openai_message = {
                "role": "tool" if message.tool_results else message.role,
                "content": list(filter(None, [
                    OpenAIProvider.content_block_to_openai_format(c) for c in message.content
                ]))
            }
            if message.tool_calls:
                try:
                    openai_message["tool_calls"] = [
                        {
                            "id": tool_call.tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_call.tool.__name__,
                                "arguments": json.dumps(tool_call.params.model_dump())
                            }
                        } for tool_call in message.tool_calls
                    ]
                except TypeError as e:
                    print(f"Error serializing tool calls: {e}. Did you fully type your @ell.tool decorated functions?")
                    raise
                openai_message["content"] = None  # Set content to null when there are tool calls

            if message.tool_results:
                openai_message["tool_call_id"] = message.tool_results[0].tool_call_id
                openai_message["content"] = message.tool_results[0].result[0].text
                assert len(message.tool_results[0].result) == 1, "Tool result should only have one content block"
                assert message.tool_results[0].result[0].type == "text", "Tool result should only have one text content block"
            return openai_message

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
            openai_messages = [cls.message_to_openai_format(message) for message in messages]

            actual_n = api_params.get("n", 1)
            final_call_params["model"] = model
            final_call_params["messages"] = openai_messages

            if model == "o1-preview" or model == "o1-mini":
                # Ensure no system messages are present
                assert all(msg['role'] != 'system' for msg in final_call_params['messages']), "System messages are not allowed for o1-preview or o1-mini models"
                
                response = client.chat.completions.create(**final_call_params)
                final_call_params.pop("stream", None)
                final_call_params.pop("stream_options", None)


            elif final_call_params.get("response_format"):
                final_call_params.pop("stream", None)
                final_call_params.pop("stream_options", None)
                response = client.beta.chat.completions.parse(**final_call_params)
            else:
                # Tools not workign with structured API
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
                    final_call_params.pop("stream", None)
                    final_call_params.pop("stream_options", None)
                else:
                    final_call_params["stream_options"] = {"include_usage": True}
                    final_call_params["stream"] = True

                response = client.chat.completions.create(**final_call_params)
            

            return APICallResult(
                response=response,
                actual_streaming=isinstance(response, openai.Stream),
                actual_n=actual_n,
                final_call_params=final_call_params,
            )

        @classmethod
        def process_response(
            cls, call_result: APICallResult, _invocation_origin: str,  logger : Optional[Any] = None,  tools: Optional[List[LMP]] = None,
        ) -> Tuple[List[Message], Dict[str, Any]]:
            choices_progress = defaultdict(list)
            api_params = call_result.final_call_params
            metadata = {}
            #XXX: Remove logger and refactor this API

            if not call_result.actual_streaming:
                response = [call_result.response]
            else:
                response = call_result.response
            

            for chunk in response:
                if hasattr(chunk, "usage") and chunk.usage:
                    metadata = chunk.to_dict()
                    

                for choice in chunk.choices:
                    choices_progress[choice.index].append(choice)
                    
                    if  choice.index == 0 and logger:
                        # print(choice, streaming)
                        logger(choice.delta.content if call_result.actual_streaming else 
                            choice.message.content or getattr(choice.message, "refusal", ""), is_refusal=getattr(choice.message, "refusal", False) if not call_result.actual_streaming else False)



            tracked_results = []
            for _, choice_deltas in sorted(choices_progress.items(), key=lambda x: x[0]):
                content = []

                if call_result.actual_streaming:
                    text_content = "".join(
                        (choice.delta.content or "" for choice in choice_deltas)
                    )
                    if text_content:
                        content.append(
                            ContentBlock(
                                text=_lstr(
                                    content=text_content, _origin_trace=_invocation_origin
                                )
                            )
                        )

                    # Determine the role for streaming responses, defaulting to 'assistant' if not provided
                    streamed_role = next((choice.delta.role for choice in choice_deltas if choice.delta.role), 'assistant')
                else:
                    choice = choice_deltas[0].message
                    if choice.refusal:
                        raise ValueError(choice.refusal)
                    if api_params.get("response_format"):
                        content.append(ContentBlock(parsed=choice.parsed))
                    elif choice.content:
                        content.append(
                            ContentBlock(
                                text=_lstr(
                                    content=choice.content, _origin_trace=_invocation_origin
                                )
                            )
                        )

                if not call_result.actual_streaming and hasattr(choice, "tool_calls") and choice.tool_calls:
                    assert tools is not None, "Tools not provided, yet tool calls in response. Did you manually specify a tool spec without using ell.tool?"
                    for tool_call in choice.tool_calls:
                        matching_tool = next(
                            (
                                tool
                                for tool in tools
                                if tool.__name__ == tool_call.function.name
                            ),
                            None,
                        )
                        if matching_tool:
                            params = matching_tool.__ell_params_model__(
                                **json.loads(tool_call.function.arguments)
                            )
                            content.append(
                                ContentBlock(
                                    tool_call=ToolCall(
                                        tool=matching_tool,
                                        tool_call_id=_lstr(
                                            tool_call.id, _origin_trace=_invocation_origin
                                        ),
                                        params=params,
                                    )
                                )
                            )

                tracked_results.append(
                    Message(
                        role=(
                            choice.role
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
            return openai.Client


    register_provider(OpenAIProvider)
except ImportError:
    pass