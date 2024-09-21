from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
from ell.provider import  EllCallParams, Metadata, Provider
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
    from anthropic.types import Message as AnthropicMessage, MessageCreateParams, RawMessageStreamEvent
    from anthropic._streaming import Stream

    class AnthropicProvider(Provider):
           
        def provider_call_function(self, client : Anthropic, api_call_params : Optional[Dict[str, Any]] = None) -> Callable[..., Any]:
            return client.messages.create

        def translate_to_provider(self, ell_call : EllCallParams) -> Dict[str, Any]: 
            final_call_params = ell_call.api_params.copy()
            assert final_call_params.get("max_tokens") is not None, f"max_tokens is required for anthropic calls, pass it to the @ell.simple/complex decorator, e.g. @ell.simple(..., max_tokens=your_max_tokens) or pass it to the model directly as a parameter when calling your LMP: your_lmp(..., api_params=({{'max_tokens': your_max_tokens}}))."

            anthropic_messages = [message_to_anthropic_format(message) for message in ell_call.messages]
            system_message = None
            if anthropic_messages and anthropic_messages[0]["role"] == "system":
                system_message = anthropic_messages.pop(0)
            
            if system_message:
                final_call_params["system"] = system_message["content"][0]["text"]
            
            # XXX: untils streaming is implemented.
            final_call_params['stream'] = True

            final_call_params["model"] = ell_call.model
            final_call_params["messages"] = anthropic_messages

            if ell_call.tools:
                final_call_params["tools"] = [
                    {
                        "name": tool.__name__,
                        "description": tool.__doc__,
                        "input_schema": tool.__ell_params_model__.model_json_schema(),
                    }
                    for tool in ell_call.tools
                ]

            return final_call_params
    
        def translate_from_provider(
            self,
            provider_response : Union[Stream[RawMessageStreamEvent], AnthropicMessage],
            ell_call: EllCallParams,
            provider_call_params: Dict[str, Any],
            origin_id: Optional[str] = None,
            logger: Optional[Callable[..., None]] = None,
        ) -> Tuple[List[Message], Metadata]:
            
            usage = {}
            tracked_results = []
            metadata = {}

            if provider_call_params.get("stream", False):
                content = []
                current_block: Optional[Dict[str, Any]] = None
                message_metadata = {}

                with cast(Stream[RawMessageStreamEvent], provider_response) as stream:
                    for chunk in stream:
                        if chunk.type == "message_start":
                            message_metadata = chunk.message.dict()
                            message_metadata.pop("content", None)  # Remove content as we'll build it separately

                        elif chunk.type == "content_block_start":
                            current_block = chunk.content_block.dict()
                            current_block["content"] = ""

                        elif chunk.type == "content_block_delta":
                            if current_block is not None:
                                if current_block["type"] == "text":
                                    current_block["content"] += chunk.delta.text
                                    logger(chunk.delta.text)
        

                        elif chunk.type == "content_block_stop":
                            if current_block is not None:
                                if current_block["type"] == "text":
                                    content.append(ContentBlock(text=_lstr(current_block["content"],origin_trace=origin_id)))
                                elif current_block["type"] == "tool_use":
                                    try:
                                        final_cb = chunk.content_block
                                        matching_tool = ell_call.get_tool_by_name(final_cb.name)
                                        if matching_tool:
                                            content.append(
                                                ContentBlock(
                                                    tool_call=ToolCall(
                                                        tool=matching_tool,
                                                        tool_call_id=_lstr(
                                                            final_cb.id,origin_trace=origin_id
                                                        ),
                                                        params=final_cb.input,
                                                    )
                                                )
                                            )
                                        if logger:
                                            logger(f" <tool_use: {current_block['name']}(")
                                            logger(f"{final_cb.input}")
                                            logger(f")>")
                                    except json.JSONDecodeError:
                                        # Handle partial JSON if necessary
                                        pass
                            current_block = None

                        elif chunk.type == "message_delta":
                            message_metadata.update(chunk.delta.dict())
                            if chunk.usage:
                                usage.update(chunk.usage.dict())

                        elif chunk.type == "message_stop":
                            tracked_results.append(Message(role="assistant", content=content))

                        # print(chunk)
                metadata = message_metadata
            
            # process metadata for ell
            # XXX: Unify an ell metadata format for ell studio.
            usage["prompt_tokens"] = usage.get("input_tokens", 0)
            usage["completion_tokens"] = usage.get("output_tokens", 0)
            usage["total_tokens"] = usage['prompt_tokens'] + usage['completion_tokens']

            metadata["usage"] = usage
            return tracked_results, metadata

        
    register_provider(AnthropicProvider(), Anthropic)
except ImportError:
    pass

def serialize_image_for_anthropic(img):
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode()

def content_block_to_anthropic_format(content_block: ContentBlock) -> Dict[str, Any]:
    if content_block.image:
        base64_image = serialize_image_for_anthropic(content_block.image)
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
    elif content_block.tool_call:
        
        return {
            "type": "tool_use",
            "id": content_block.tool_call.tool_call_id,
            "name": content_block.tool_call.tool.__name__,
            "input": content_block.tool_call.params.model_dump()
        }
    elif content_block.tool_result:
        return {
            "type": "tool_result",
            "tool_use_id": content_block.tool_result.tool_call_id,
            "content": [content_block_to_anthropic_format(c) for c in content_block.tool_result.result]
        }
    else:
        raise ValueError("Content block is not supported by anthropic")



def message_to_anthropic_format(message: Message) -> Dict[str, Any]:
    
    anthropic_message = {
        "role": message.role,
        "content": list(filter(None, [
            content_block_to_anthropic_format(c) for c in message.content
        ]))
    }
    return anthropic_message