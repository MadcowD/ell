from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
from ell.provider import  EllCallParams, Metadata, Provider
from ell.types import Message, ContentBlock, ToolCall, ImageContent
from ell.types._lstr import _lstr
import json
from ell.configurator import config, register_provider
from ell.types.message import LMP
from ell.util.serialization import serialize_image
from io import BytesIO
import requests
from PIL import Image as PILImage

try:
    from botocore.client import BaseClient
    from botocore.eventstream import (EventStream)
    class BedrockProvider(Provider):
        dangerous_disable_validation = True

        def provider_call_function(self, client : Any, api_call_params : Optional[Dict[str, Any]] = None) -> Callable[..., Any]:
            if api_call_params and api_call_params.get("stream", False):
                api_call_params.pop('stream')
                return client.converse_stream
            else:
                return client.converse

        def translate_to_provider(self, ell_call : EllCallParams):
            final_call_params = {}

            if ell_call.api_params.get('api_params',{}).get('stream', False):
                final_call_params['stream'] = ell_call.api_params.get('api_params',{}).get('stream', False)

            bedrock_converse_messages = [message_to_bedrock_message_format(message) for message in ell_call.messages]

            system_message = None
            if bedrock_converse_messages and bedrock_converse_messages[0]["role"] == "system":
                system_message = bedrock_converse_messages.pop(0)

            if system_message:
                final_call_params["system"] = [{'text':system_message["content"][0]["text"]}]

            final_call_params["modelId"] = ell_call.model
            final_call_params["messages"] = bedrock_converse_messages

            if ell_call.tools:
                tools = [
                    #XXX: Cleaner with LMP's as a class.
                    dict(
                        toolSpec = dict(
                            name=tool.__name__,
                            description=tool.__doc__,
                            inputSchema=dict(
                                json=tool.__ell_params_model__.model_json_schema(),
                            )
                        )
                    )
                    for tool in ell_call.tools
                ]
                final_call_params["toolConfig"] = {'tools':tools}

            return final_call_params

        def translate_from_provider(
                self,
                provider_response: Union[EventStream, Any],
                ell_call: EllCallParams,
                provider_call_params: Dict[str, Any],
                origin_id: Optional[str] = None,
                logger: Optional[Callable[..., None]] = None,
            ) -> Tuple[List[Message], Metadata]:

            usage = {}
            metadata : Metadata = {}

            metadata : Metadata = {}
            tracked_results : List[Message] = []
            did_stream = ell_call.api_params.get("api_params", {}).get('stream')

            if did_stream:
                content = []
                current_block: Optional[Dict[str, Any]] = {}
                message_metadata = {}
                for chunk in provider_response.get('stream'):

                    if "messageStart" in chunk:
                        current_block['content'] = ''
                        pass
                    elif "contentBlockStart" in chunk:
                        pass
                    elif "contentBlockDelta" in chunk:
                        delta = chunk.get("contentBlockDelta", {}).get("delta", {})
                        if "text" in delta:
                            current_block['type'] = 'text'
                            current_block['content'] += delta.get("text")
                            if logger:
                                logger(delta.get("text"))
                        else:
                            pass
                    elif "contentBlockStop" in chunk:
                        if current_block is not None:
                            if current_block["type"] == "text":
                                content.append(ContentBlock(text=_lstr(content=content, origin_trace=origin_id)))

                    elif "messageStop" in chunk:
                        tracked_results.append(Message(role="assistant", content=content))

                    elif "metadata" in chunk:
                        if "usage" in chunk["metadata"]:
                            usage["prompt_tokens"] = chunk["metadata"].get('usage').get("inputTokens", 0)
                            usage["completion_tokens"] = chunk["metadata"].get('usage').get("outputTokens", 0)
                            usage["total_tokens"] = usage['prompt_tokens'] + usage['completion_tokens']
                            message_metadata["usage"] = usage
                    else:
                        pass


                metadata = message_metadata
            else:
                # Non-streaming response processing (unchanged)
                cbs = []
                for content_block in provider_response.get('output', {}).get('message', {}).get('content', []):
                    if 'text' in content_block:
                        cbs.append(ContentBlock(text=_lstr(content_block.get('text'), origin_trace=origin_id)))
                    elif 'toolUse' in content_block:
                        assert ell_call.tools is not None, "Tools were not provided to the model when calling it and yet bedrock returned a tool use."
                        try:
                            toolUse = content_block['toolUse']
                            matching_tool = ell_call.get_tool_by_name(toolUse["name"])
                            if matching_tool:
                                cbs.append(
                                    ContentBlock(
                                        tool_call=ToolCall(
                                            tool=matching_tool,
                                            tool_call_id=_lstr(
                                                toolUse['toolUseId'],origin_trace=origin_id
                                            ),
                                            params=toolUse['input'],
                                        )
                                    )
                                )
                        except json.JSONDecodeError:
                            if logger: logger(f" - FAILED TO PARSE JSON")
                            pass
                tracked_results.append(Message(role="assistant", content=cbs))
                if logger:
                    logger(tracked_results[0].text)


                # usage = call_result.response.usage.dict() if call_result.response.get('usage') else {}
                # metadata = call_result.response.model_dump()
                # del metadata["content"]

            # process metadata for ell
            # XXX: Unify an ell metadata format for ell studio.
            usage["prompt_tokens"] = usage.get("inputTokens", 0)
            usage["completion_tokens"] = usage.get("outputTokens", 0)
            usage["total_tokens"] = usage['prompt_tokens'] + usage['completion_tokens']

            metadata["usage"] = usage
            return tracked_results, metadata


    # XXX: Make a singleton.
    register_provider(BedrockProvider(), BaseClient)
except ImportError:
    pass


def content_block_to_bedrock_format(content_block: ContentBlock) -> Dict[str, Any]:
    if content_block.image:
        img:ImageContent = content_block.image
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
        base64_image = buffer.getvalue()
        return {
            "image": {
                "format": "png",
                "source":
                {
                    "bytes": base64_image
                }
            }
        }
    elif content_block.text:
        return {
            "text": content_block.text
        }
    elif content_block.parsed:
        return {
            "type": "text",
            "text": json.dumps(content_block.parsed.model_dump(), ensure_ascii=False)
        }
    elif content_block.tool_call:
        return {
            "toolUse": {
                "toolUseId": content_block.tool_call.tool_call_id,
                "name": content_block.tool_call.tool.__name__,
                "input": content_block.tool_call.params.model_dump()
            }
        }
    elif content_block.tool_result:
        return {
            "toolResult":{
                "toolUseId": content_block.tool_result.tool_call_id,
                "content": [content_block_to_bedrock_format(c) for c in content_block.tool_result.result]
            }
        }
    else:
        raise ValueError("Content block is not supported by bedrock")



def message_to_bedrock_message_format(message: Message) -> Dict[str, Any]:

    converse_message = {
        "role": message.role,
        "content": list(filter(None, [
            content_block_to_bedrock_format(c) for c in message.content
        ]))
    }
    return converse_message