from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

from pydantic import BaseModel
from ell.provider import  EllCallParams, Metadata, Provider
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
import json
from ell.configurator import _Model, config, register_provider
from ell.types.message import LMP
from ell.util.serialization import serialize_image

try: 
    # XXX: Could genericize.
    import openai
    from openai._streaming import Stream
    from openai.types.chat import ChatCompletion, ParsedChatCompletion, ChatCompletionChunk, ChatCompletionMessageParam

    class OpenAIProvider(Provider):
        dangerous_disable_validation = True
        
        def provider_call_function(self, client : openai.Client, api_call_params : Optional[Dict[str, Any]] = None) -> Callable[..., Any]:
            if api_call_params and (isinstance(fmt := api_call_params.get("response_format"), type)) and issubclass(fmt, BaseModel):
                return client.beta.chat.completions.parse
            else:
                return client.chat.completions.create
            
        def translate_to_provider(self, ell_call : EllCallParams) -> Dict[str, Any]: 
            final_call_params = ell_call.api_params.copy()
            final_call_params["model"] = ell_call.model
            # Stream by default for verbose logging.
            final_call_params["stream"] = True
            final_call_params["stream_options"] = {"include_usage": True}

            # XXX: Deprecation of config.registry.supports_streaming when streaming is implemented.
            if ell_call.tools or final_call_params.get("response_format") or (regisered_model := config.registry.get(ell_call.model, None)) and regisered_model.supports_streaming is False:
                final_call_params.pop("stream", None)
                final_call_params.pop("stream_options", None)
            if ell_call.tools:
                final_call_params.update(
                    tool_choice="auto",
                    tools=[  
                        dict(
                            type="function",
                            function=dict(
                                name=tool.__name__,
                                description=tool.__doc__,
                                parameters=tool.__ell_params_model__.model_json_schema(),  #type: ignore
                            )
                        ) for tool in ell_call.tools
                    ]
                )
            # messages
            openai_messages : List[ChatCompletionMessageParam] = []
            for message in ell_call.messages:
                if (tool_calls := message.tool_calls):
                    assert message.role == "assistant", "Tool calls must be from the assistant."
                    assert all(t.tool_call_id for t in tool_calls), "Tool calls must have tool call ids."
                    openai_messages.append(dict(
                        tool_calls=[
                            dict(
                                id=cast(str, tool_call.tool_call_id),
                                type="function",
                                function=dict(
                                    name=tool_call.tool.__name__,
                                    arguments=json.dumps(tool_call.params.model_dump())
                                )
                            ) for tool_call in tool_calls ],
                        role="assistant",
                        content=None,
                    ))
                elif (tool_results := message.tool_results):
                    for tool_result in tool_results:
                        assert all(cb.type == "text" for cb in tool_result.result), "Tool result does not match expected content blocks."
                        openai_messages.append(dict(
                            role="tool",
                            tool_call_id=tool_result.tool_call_id,
                            content=tool_result.text_only, 
                        ))
                else:
                    openai_messages.append(cast(ChatCompletionMessageParam, dict(
                        role=message.role,
                        content=[_content_block_to_openai_format(c) for c in message.content] 
                             if message.role != "system" 
                             else message.text_only
                    )))
                     
            final_call_params["messages"] = openai_messages
            
            return final_call_params
        
        def translate_from_provider(
            self,
            provider_response: Union[
                ChatCompletion, 
                ParsedChatCompletion,
                Stream[ChatCompletionChunk], Any],
            ell_call: EllCallParams,
            provider_call_params: Dict[str, Any],
            origin_id: Optional[str] = None,
            logger: Optional[Callable[..., None]] = None,
        ) -> Tuple[List[Message], Metadata]:
            
            metadata : Metadata = {} 
            messages : List[Message] = []
            did_stream = provider_call_params.get("stream", False)

        
            if did_stream:
                stream = cast(Stream[ChatCompletionChunk], provider_response)
                message_streams = defaultdict(list)
                role : Optional[str] = None
                for chunk in stream: 
                    metadata.update(chunk.model_dump(exclude={"choices"})) 
                    
                    for chat_compl_chunk in chunk.choices:
                        message_streams[chat_compl_chunk.index].append(chat_compl_chunk)
                        delta = chat_compl_chunk.delta
                        role = role or delta.role
                        if  chat_compl_chunk.index == 0 and logger:
                            logger(delta.content, is_refusal=hasattr(delta, "refusal") and delta.refusal)
                for _, message_stream in sorted(message_streams.items(), key=lambda x: x[0]):
                    text = "".join((choice.delta.content or "") for choice in message_stream)
                    messages.append(
                        Message(role=role, 
                                content=_lstr(content=text,origin_trace=origin_id)))
                    #XXX: Support streaming other types.
            else:
                chat_completion = cast(Union[ChatCompletion, ParsedChatCompletion], provider_response)
                metadata = chat_completion.model_dump(exclude={"choices"})
                for oai_choice in chat_completion.choices: 
                    role = oai_choice.message.role
                    content_blocks = []
                    if (hasattr(message := oai_choice.message, "refusal") and (refusal := message.refusal)):
                        raise ValueError(refusal)
                    if hasattr(message, "parsed"):
                        if (parsed := message.parsed): 
                            content_blocks.append(ContentBlock(parsed=parsed)) #XXX: Origin tracing
                            if logger: logger(parsed.model_dump_json())
                    else:
                        if (content := message.content):
                            content_blocks.append(
                                ContentBlock(
                                    text=_lstr(content=content,origin_trace=origin_id)))
                            if logger: logger(content)
                        if (tool_calls := message.tool_calls):
                            for tool_call in tool_calls:
                                matching_tool = ell_call.get_tool_by_name(tool_call.function.name)
                                assert matching_tool, "Model called tool not found in provided toolset."
                                content_blocks.append(
                                    ContentBlock(
                                        tool_call=ToolCall(
                                            tool=matching_tool,
                                            tool_call_id=_lstr(
                                                tool_call.id, origin_trace= origin_id),
                                            params=json.loads(tool_call.function.arguments),
                                        )
                                    )
                                )
                                if logger: logger(repr(tool_call))
                    messages.append(Message(role=role, content=content_blocks))
            return messages, metadata


    # xx: singleton needed
    openai_provider = OpenAIProvider()
    register_provider(openai_provider, openai.Client)
except ImportError:
    pass

def _content_block_to_openai_format(content_block: ContentBlock) -> Dict[str, Any]:
    if (image := content_block.image):
        image_url = dict(url=serialize_image(image.image) if image.image else image.url)
        # XXX: Solve per content params better
        if image.detail: image_url["detail"] = image.detail
        return {
            "type": "image_url",
            "image_url": image_url
        }
    elif ((text := content_block.text) is not None): return dict(type="text", text=text)
    elif (parsed := content_block.parsed): return dict(type="text", text=parsed.model_dump_json())    
    else:
        raise ValueError(f"Unsupported content block type for openai: {content_block}")