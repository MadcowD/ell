from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
from ell2a.provider import Ell2aCallParams, Metadata, Provider
from ell2a.types import Message, ContentBlock, AgentCall, ImageContent
from ell2a.types._lstr import _lstr
import json
from ell2a.configurator import config, register_provider
from ell2a.types.message import LMP
from ell2a.util.serialization import serialize_image
from io import BytesIO
import requests
from PIL import Image as PILImage

try:
    from botocore.client import BaseClient
    from botocore.eventstream import (EventStream)

    class BedrockProvider(Provider):
        dangerous_disable_validation = True

        def provider_call_function(self, client: Any, api_call_params: Optional[Dict[str, Any]] = None) -> Callable[..., Any]:
            if api_call_params and api_call_params.get("stream", False):
                api_call_params.pop('stream')
                return client.converse_stream
            else:
                return client.converse

        def translate_to_provider(self, ell2a_call: Ell2aCallParams):
            final_call_params = {}

            if ell2a_call.api_params.get('api_params', {}).get('stream', False):
                final_call_params['stream'] = ell2a_call.api_params.get(
                    'api_params', {}).get('stream', False)

            bedrock_converse_messages = [message_to_bedrock_message_format(
                message) for message in ell2a_call.messages]

            system_message = None
            if bedrock_converse_messages and bedrock_converse_messages[0]["role"] == "system":
                system_message = bedrock_converse_messages.pop(0)

            if system_message:
                final_call_params["system"] = [
                    {'text': system_message["content"][0]["text"]}]

            final_call_params["modelId"] = ell2a_call.model
            final_call_params["messages"] = bedrock_converse_messages

            if ell2a_call.agents:
                agents = [
                    # XXX: Cleaner with LMP's as a class.
                    dict(
                        agentSpec=dict(
                            name=agent.__name__,
                            description=agent.__doc__,
                            inputSchema=dict(
                                json=agent.__ell2a_params_model__.model_json_schema(),
                            )
                        )
                    )
                    for agent in ell2a_call.agents
                ]
                final_call_params["agentConfig"] = {'agents': agents}

            return final_call_params

        def translate_from_provider(
            self,
            provider_response: Union[EventStream, Any],
            ell2a_call: Ell2aCallParams,
            provider_call_params: Dict[str, Any],
            origin_id: Optional[str] = None,
            logger: Optional[Callable[..., None]] = None,
        ) -> Tuple[List[Message], Metadata]:

            usage = {}
            metadata: Metadata = {}

            metadata: Metadata = {}
            tracked_results: List[Message] = []
            did_stream = ell2a_call.api_params.get(
                "api_params", {}).get('stream')

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
                        delta = chunk.get("contentBlockDelta",
                                          {}).get("delta", {})
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
                                content.append(ContentBlock(text=_lstr(
                                    content=content, origin_trace=origin_id)))

                    elif "messageStop" in chunk:
                        tracked_results.append(
                            Message(role="assistant", content=content))

                    elif "metadata" in chunk:
                        if "usage" in chunk["metadata"]:
                            usage["prompt_tokens"] = chunk["metadata"].get(
                                'usage').get("inputTokens", 0)
                            usage["completion_tokens"] = chunk["metadata"].get(
                                'usage').get("outputTokens", 0)
                            usage["total_tokens"] = usage['prompt_tokens'] + \
                                usage['completion_tokens']
                            message_metadata["usage"] = usage
                    else:
                        pass

                metadata = message_metadata
            else:
                # Non-streaming response processing (unchanged)
                cbs = []
                for content_block in provider_response.get('output', {}).get('message', {}).get('content', []):
                    if 'text' in content_block:
                        cbs.append(ContentBlock(text=_lstr(
                            content_block.get('text'), origin_trace=origin_id)))
                    elif 'agentUse' in content_block:
                        assert ell2a_call.agents is not None, "Agents were not provided to the model when calling it and yet bedrock returned a agent use."
                        try:
                            agentUse = content_block['agentUse']
                            matching_agent = ell2a_call.get_agent_by_name(
                                agentUse["name"])
                            if matching_agent:
                                cbs.append(
                                    ContentBlock(
                                        agent_call=AgentCall(
                                            agent=matching_agent,
                                            agent_call_id=_lstr(
                                                agentUse['agentUseId'], origin_trace=origin_id
                                            ),
                                            params=agentUse['input'],
                                        )
                                    )
                                )
                        except json.JSONDecodeError:
                            if logger:
                                logger(f" - FAILED TO PARSE JSON")
                            pass
                tracked_results.append(Message(role="assistant", content=cbs))
                if logger:
                    logger(tracked_results[0].text)

                # usage = call_result.response.usage.dict() if call_result.response.get('usage') else {}
                # metadata = call_result.response.model_dump()
                # del metadata["content"]

            # process metadata for ell2a
            # XXX: Unify an ell2a metadata format for ell2a studio.
            usage["prompt_tokens"] = usage.get("inputTokens", 0)
            usage["completion_tokens"] = usage.get("outputTokens", 0)
            usage["total_tokens"] = usage['prompt_tokens'] + \
                usage['completion_tokens']

            metadata["usage"] = usage
            return tracked_results, metadata

    # XXX: Make a singleton.
    register_provider(BedrockProvider(), BaseClient)
except ImportError:
    pass


def content_block_to_bedrock_format(content_block: ContentBlock) -> Dict[str, Any]:
    if content_block.image:
        img: ImageContent = content_block.image
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
    elif content_block.agent_call:
        return {
            "agentUse": {
                "agentUseId": content_block.agent_call.agent_call_id,
                "name": content_block.agent_call.agent.__name__,
                "input": content_block.agent_call.params.model_dump()
            }
        }
    elif content_block.agent_result:
        return {
            "agentResult": {
                "agentUseId": content_block.agent_result.agent_call_id,
                "content": [content_block_to_bedrock_format(c) for c in content_block.agent_result.result]
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
