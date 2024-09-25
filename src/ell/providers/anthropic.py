from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union, cast
from ell.provider import  EllCallParams, Metadata, Provider
from ell.types import Message, ContentBlock, ToolCall, ImageContent

from ell.types._lstr import _lstr
from ell.types.message import LMP
from ell.configurator import register_provider
from ell.util.serialization import serialize_image
import base64
from io import BytesIO
import json
import requests
from PIL import Image as PILImage

try:
    import anthropic
    from anthropic import Anthropic
    from anthropic.types import Message as AnthropicMessage, MessageParam, RawMessageStreamEvent
    from anthropic.types.message_create_params import MessageCreateParamsStreaming
    from anthropic._streaming import Stream

    class AnthropicProvider(Provider):
        dangerous_disable_validation = True
           
        def provider_call_function(self, client : Anthropic, api_call_params : Optional[Dict[str, Any]] = None) -> Callable[..., Any]:
            return client.messages.create

        def translate_to_provider(self, ell_call : EllCallParams): 
            final_call_params = cast(MessageCreateParamsStreaming, ell_call.api_params.copy())
            # XXX: Helper, but should be depreicated due to ssot
            assert final_call_params.get("max_tokens") is not None, f"max_tokens is required for anthropic calls, pass it to the @ell.simple/complex decorator, e.g. @ell.simple(..., max_tokens=your_max_tokens) or pass it to the model directly as a parameter when calling your LMP: your_lmp(..., api_params=({{'max_tokens': your_max_tokens}}))."

            dirty_msgs = [
                MessageParam(
                    role=cast(Literal["user", "assistant"], message.role), 
                    content=[_content_block_to_anthropic_format(c) for c in message.content]) for message in ell_call.messages]
            role_correct_msgs   : List[MessageParam] = []
            for msg in dirty_msgs:
                if (not len(role_correct_msgs) or role_correct_msgs[-1]['role'] != msg['role']):
                    role_correct_msgs.append(msg)
                else: cast(List, role_correct_msgs[-1]['content']).extend(msg['content'])
            
            system_message = None
            if role_correct_msgs and role_correct_msgs[0]["role"] == "system":
                system_message = role_correct_msgs.pop(0)
            
            if system_message:
                final_call_params["system"] = system_message["content"][0]["text"]

            
            final_call_params['stream'] = True
            final_call_params["model"] = ell_call.model
            final_call_params["messages"] = role_correct_msgs

            if ell_call.tools:
                final_call_params["tools"] = [
                    #XXX: Cleaner with LMP's as a class.
                    dict(
                        name=tool.__name__,
                        description=tool.__doc__,
                        input_schema=tool.__ell_params_model__.model_json_schema(),
                    )
                    for tool in ell_call.tools
                ]

            # print(final_call_params)
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

            #XXX: Support n > 0

            if provider_call_params.get("stream", False):
                content = []
                current_blocks: Dict[int, Dict[str, Any]] = {}
                message_metadata = {}

                with cast(Stream[RawMessageStreamEvent], provider_response) as stream:
                    for chunk in stream:
                        if chunk.type == "message_start":
                            message_metadata = chunk.message.model_dump()
                            message_metadata.pop("content", None)  # Remove content as we'll build it separately

                        elif chunk.type == "content_block_start":
                            block = chunk.content_block.model_dump()
                            current_blocks[chunk.index] = block
                            if block["type"] == "tool_use":
                                if logger: logger(f" <tool_use: {block['name']}(")
                                block["input"] = "" # force it to be a string, XXX: can implement partially parsed json later.
                        elif chunk.type == "content_block_delta":
                            if chunk.index in current_blocks:
                                block = current_blocks[chunk.index]
                                if (delta := chunk.delta).type == "text_delta":
                                    block["text"] += delta.text
                                    if logger: logger(delta.text)
                                if delta.type == "input_json_delta":
                                    block["input"] += delta.partial_json
                                    if logger: logger(delta.partial_json)

                        elif chunk.type == "content_block_stop":
                            if chunk.index in current_blocks:
                                block = current_blocks.pop(chunk.index)
                                if block["type"] == "text":
                                    content.append(ContentBlock(text=_lstr(block["text"],origin_trace=origin_id)))
                                elif block["type"] == "tool_use":
                                    try:
                                        matching_tool = ell_call.get_tool_by_name(block["name"])
                                        if matching_tool:
                                            content.append(
                                                ContentBlock(
                                                    tool_call=ToolCall(
                                                        tool=matching_tool,
                                                        tool_call_id=_lstr(
                                                            block['id'],origin_trace=origin_id
                                                        ),
                                                        params=json.loads(block['input']) if block['input'] else {},
                                                    )
                                                )
                                            )
                                    except json.JSONDecodeError:
                                        if logger: logger(f" - FAILED TO PARSE JSON")
                                        pass
                                    if logger: logger(f")>")

                        elif chunk.type == "message_delta":
                            message_metadata.update(chunk.delta.model_dump())
                            if chunk.usage:
                                usage.update(chunk.usage.model_dump())

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

    # XXX: Make a singleton.
    anthropic_provider = AnthropicProvider()
    register_provider(anthropic_provider, anthropic.Anthropic)
    register_provider(anthropic_provider, anthropic.AnthropicBedrock)
    register_provider(anthropic_provider, anthropic.AnthropicVertex)

except ImportError:
    pass

def serialize_image_for_anthropic(img : ImageContent):
    if img.url:
        # Download the image from the URL
        response = requests.get(img.url)
        response.raise_for_status()  # Raise an exception for bad responses
        pil_image = PILImage.open(BytesIO(response.content))
    elif img.image:
        pil_image = img.image
    else:
        raise ValueError("Image object has neither url nor image data.")
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    base64_image =  base64.b64encode(buffer.getvalue()).decode()
    return dict(
        type="image",
        source=dict(
            type="base64",
            media_type="image/png",
            data=base64_image
        )
    )

def _content_block_to_anthropic_format(content_block: ContentBlock):
        if (image := content_block.image): return serialize_image_for_anthropic(image)
        elif ((text := content_block.text) is not None): return dict(type="text", text=text)
        elif (parsed := content_block.parsed):
            return dict(type="text", text=json.dumps(parsed.model_dump()))
        elif (tool_call := content_block.tool_call):
            return dict(
                type="tool_use",
                id=tool_call.tool_call_id,
                name=tool_call.tool.__name__,
                input=tool_call.params.model_dump()
            )
        elif (tool_result := content_block.tool_result):
            return dict(
                type="tool_result",
                tool_use_id=tool_result.tool_call_id,
                content=[_content_block_to_anthropic_format(c) for c in tool_result.result]
            )
        else:
            raise ValueError("Content block is not supported by anthropic")
