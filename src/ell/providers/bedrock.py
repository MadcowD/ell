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
    import boto3

    class BedrockProvider(Provider):
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

            final_call_params.pop('provider')

            bedrock_converse_messages = [message_to_bedrock_message_format(message) for message in messages]

            system_message = None
            if bedrock_converse_messages and bedrock_converse_messages[0]["role"] == "system":
                system_message = bedrock_converse_messages.pop(0)

            if system_message:
                final_call_params["system"] = [{'text':system_message["content"][0]["text"]}]

            actual_n = api_params.get("n", 1)

            final_call_params["modelId"] = model
            final_call_params["messages"] = bedrock_converse_messages


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
            # XXX: Support soon.
            stream = True
            if stream:
                bedrock_response = client.converse_stream(**final_call_params)
                response = bedrock_response
            else:
                bedrock_response = client.converse(**final_call_params)
                if 'output' not in bedrock_response:
                    raise ValueError("No output received from Bedrock model")
                else:
                    response = bedrock_response['output']

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
            usage = {}
            tracked_results = []
            metadata = {}

            if call_result.actual_streaming:
                content = []
                current_block: Optional[Dict[str, Any]] = {}
                message_metadata = {}

                for chunk in call_result.response.get('stream'):

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
                                content.append(ContentBlock(text=_lstr(current_block["content"], _origin_trace=_invocation_origin)))

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
                for content_block in call_result.response.get('message', {}).get('content', []):
                    if 'text' in content_block:
                        cbs.append(ContentBlock(text=_lstr(content_block.get('text'), _origin_trace=_invocation_origin)))
                    elif 'toolUse' in content_block:
                        assert tools is not None, "Tools were not provided to the model when calling it and yet bedrock returned a tool use."
                        tool_call = ToolCall(
                            tool=next((t for t in tools if t.__name__ == content_block.get('name')), None) ,
                            tool_call_id=content_block.id,
                            params=content_block.input
                        )
                        cbs.append(ContentBlock(tool_call=tool_call))
                tracked_results.append(Message(role="assistant", content=cbs))
                if logger:
                    logger(tracked_results[0].text)


                usage = call_result.response.usage.dict() if call_result.response.get('usage') else {}
                # metadata = call_result.response.model_dump()
                # del metadata["content"]

            # process metadata for ell
            # XXX: Unify an ell metadata format for ell studio.
            usage["prompt_tokens"] = usage.get("inputTokens", 0)
            usage["completion_tokens"] = usage.get("outputTokens", 0)
            usage["total_tokens"] = usage['prompt_tokens'] + usage['completion_tokens']

            metadata["usage"] = usage
            return tracked_results, metadata

        @classmethod
        def supports_streaming(cls) -> bool:
            return True

        @classmethod
        def get_client_type(cls) -> Type:
            return boto3.client('bedrock-runtime')

        @staticmethod
        def serialize_image_for_bedrock(img):
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode()


    register_provider(BedrockProvider)
except ImportError:
    pass


def content_block_to_bedrock_format(content_block: ContentBlock) -> Dict[str, Any]:
    if content_block.image:
        base64_image = ""#AnthropicProvider.serialize_image_for_anthropic(content_block.image)
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
            "content": [content_block_to_bedrock_format(c) for c in content_block.tool_result.result]
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