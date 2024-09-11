from typing import Any, Dict, List, Optional, Tuple, Type
from ell.provider import APICallResult, Provider
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
from ell.types.message import LMP
from ell.configurator import register_provider
from ell.util.serialization import serialize_image
import base64
from io import BytesIO
import json

try:
    import anthropic
    from anthropic import Anthropic

    class AnthropicProvider(Provider):
        @classmethod
        def call_model(
            cls,
            client: Anthropic,
            model: str,
            messages: List[Message],
            api_params: Dict[str, Any],
            tools: Optional[list[LMP]] = None,
        ) -> APICallResult:
            final_call_params = api_params.copy()
            assert final_call_params.get("max_tokens") is not None, f"max_tokens is required for anthropic calls, pass it to the @ell.simple/complex decorator, e.g. @ell.simple(..., max_tokens=your_max_tokens) or pass it to the model directly as a parameter when calling your LMP: your_lmp(..., lm_params=({{'max_tokens': your_max_tokens}}))."

            anthropic_messages = [message_to_anthropic_format(message) for message in messages]
            system_message = None
            if anthropic_messages and anthropic_messages[0]["role"] == "system":
                system_message = anthropic_messages.pop(0)
            

            if system_message:
                final_call_params["system"] = system_message["content"][0]["text"]
            

            actual_n = api_params.get("n", 1)
            final_call_params["model"] = model
            final_call_params["messages"] = anthropic_messages

            if tools:
                final_call_params["tools"] = [
                    {
                        "name": tool.__name__,
                        "description": tool.__doc__,
                        "input_schema": tool.__ell_params_model__.model_json_schema(),
                    }
                    for tool in tools
                ]

            # Streaming unsupported.
            stream = final_call_params.pop("stream", False)
            if stream:
                response = client.messages.stream(**final_call_params)
            else:
                response = client.messages.create(**final_call_params)

            return APICallResult(
                response=response,
                actual_streaming=stream,
                actual_n=actual_n,
                final_call_params=final_call_params,
            )

        @classmethod
        def process_response(
            cls, call_result: APICallResult, _invocation_origin: str, logger: Optional[Any] = None, tools: Optional[List[LMP]] = None,
        ) -> Tuple[List[Message], Dict[str, Any]]:
            metadata = {}
            tracked_results = []

            if call_result.actual_streaming:
                content = []
                current_block = None
                message_metadata = {}

                for chunk in call_result.response:
                    if chunk.type == "message_start":
                        message_metadata = chunk.message.dict()
                        message_metadata.pop("content", None)  # Remove content as we'll build it separately

                    elif chunk.type == "content_block_start":
                        current_block = {"type": chunk.content_block.type, "content": ""}

                    elif chunk.type == "content_block_delta":
                        if current_block["type"] == "text":
                            current_block["content"] += chunk.delta.text
                        elif current_block["type"] == "tool_use":
                            current_block.setdefault("input", "")
                            current_block["input"] += chunk.delta.partial_json

                    elif chunk.type == "content_block_stop":
                        if current_block["type"] == "text":
                            content.append(ContentBlock(text=_lstr(current_block["content"], _origin_trace=_invocation_origin)))
                        elif current_block["type"] == "tool_use":
                            try:
                                tool_input = json.loads(current_block["input"])
                                tool_call = ToolCall(
                                    tool=next((t for t in tools if t.__name__ == current_block["name"]), None),
                                    tool_call_id=current_block.get("id"),
                                    params=tool_input
                                )
                                content.append(ContentBlock(tool_call=tool_call))
                            except json.JSONDecodeError:
                                # Handle partial JSON if necessary
                                pass
                        current_block = None

                    elif chunk.type == "message_delta":
                        message_metadata.update(chunk.delta.dict())
                        if chunk.usage:
                            metadata.update(chunk.usage.dict())

                    elif chunk.type == "message_stop":
                        tracked_results.append(Message(role="assistant", content=content, **message_metadata))

                    if logger and current_block and current_block["type"] == "text":
                        logger(chunk.delta.text)

            else:
                # Non-streaming response processing (unchanged)
                cbs = []
                for content_block in call_result.response.content:
                    if content_block.type == "text":
                        cbs.append(ContentBlock(text=_lstr(content_block.text, _origin_trace=_invocation_origin)))
                    elif content_block.type == "tool_use":
                        assert tools is not None, "Tools were not provided to the model when calling it and yet anthropic returned a tool use."
                        tool_call = ToolCall(
                            tool=next((t for t in tools if t.__name__ == content_block.name), None),
                            tool_call_id=content_block.id,
                            params=content_block.input
                        )
                        cbs.append(ContentBlock(tool_call=tool_call))
                tracked_results.append(Message(role="assistant", content=cbs))
                if logger:
                    logger(tracked_results[0].text)
                
                metadata = call_result.response.usage.dict() if call_result.response.usage else {}

            return tracked_results, metadata

        @classmethod
        def supports_streaming(cls) -> bool:
            return True

        @classmethod
        def get_client_type(cls) -> Type:
            return Anthropic
        
        @staticmethod
        def serialize_image_for_anthropic(img):
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode()
        
    register_provider(AnthropicProvider)
except ImportError:
    pass

"""
HELPERS
"""
def content_block_to_anthropic_format(content_block: ContentBlock) -> Dict[str, Any]:
    if content_block.image:
        base64_image = AnthropicProvider.serialize_image_for_anthropic(content_block.image)
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64_image
            }
        }
    elif content_block.text:
        return {
            "type": "text",
            "text": content_block.text
        }
    elif content_block.parsed:
        return {
            "type": "text",
            "text": json.dumps(content_block.parsed.model_dump())
        }
    else:
        return None


def message_to_anthropic_format(message: Message) -> Dict[str, Any]:
    
    anthropic_message = {
        "role": message.role,
        "content": list(filter(None, [
            content_block_to_anthropic_format(c) for c in message.content
        ]))
    }
    return anthropic_message