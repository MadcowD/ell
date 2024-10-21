from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

from pydantic import BaseModel
from ell2a.provider import Ell2aCallParams, Metadata, Provider
from ell2a.types import Message, ContentBlock, AgentCall
from ell2a.types._lstr import _lstr
import json
from ell2a.configurator import _Model, config, register_provider
from ell2a.types.message import LMP
from ell2a.util.serialization import serialize_image


from typing import List, Optional
from pydantic import BaseModel
from openai.types.chat import ChatCompletionMessage


class Ell2aAgentCall(BaseModel):
    agent_call_id: str
    name: str
    arguments: str


class Ell2aChatCompletionMessage(BaseModel):
    original_message: ChatCompletionMessage
    agent_calls: List[Ell2aAgentCall] = []

    @classmethod
    def from_chat_completion_message(cls, message: ChatCompletionMessage) -> 'Ell2aChatCompletionMessage':
        agent_calls = []
        if hasattr(message, 'function_call') and message.function_call:
            agent_calls.append(Ell2aAgentCall(
                agent_call_id=message.function_call.id,
                name=message.function_call.name,
                arguments=message.function_call.arguments
            ))
        elif hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.type == 'function':
                    agent_calls.append(Ell2aAgentCall(
                        agent_call_id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments
                    ))

        return cls(original_message=message, agent_calls=agent_calls)

    @property
    def content(self) -> Optional[str]:
        return self.original_message.content

    @property
    def role(self) -> str:
        return self.original_message.role

    @property
    def refusal(self) -> Optional[str]:
        return getattr(self.original_message, 'refusal', None)

    @property
    def parsed(self):
        return getattr(self.original_message, 'parsed', None)


try:
    # XXX: Could genericize.
    import openai
    from openai._streaming import Stream
    from openai.types.chat import ChatCompletion, ParsedChatCompletion, ChatCompletionChunk, ChatCompletionMessageParam

    class OpenAIProvider(Provider):
        dangerous_disable_validation = True

        def provider_call_function(self, client: openai.Client, api_call_params: Optional[Dict[str, Any]] = None) -> Callable[..., Any]:
            if api_call_params and (isinstance(fmt := api_call_params.get("response_format"), type)) and issubclass(fmt, BaseModel):
                return client.beta.chat.completions.parse
            else:
                return client.chat.completions.create

        def translate_to_provider(self, ell2a_call: Ell2aCallParams) -> Dict[str, Any]:
            final_call_params = ell2a_call.api_params.copy()
            final_call_params["model"] = ell2a_call.model
            # Stream by default for verbose logging.
            final_call_params["stream"] = True
            final_call_params["stream_options"] = {"include_usage": True}

            # XXX: Deprecation of config.registry.supports_streaming when streaming is implemented.
            if ell2a_call.agents or final_call_params.get("response_format") or (regisered_model := config.registry.get(ell2a_call.model, None)) and regisered_model.supports_streaming is False:
                final_call_params.pop("stream", None)
                final_call_params.pop("stream_options", None)
            if ell2a_call.agents:
                final_call_params.update(
                    agent_choice=final_call_params.get("agent_choice", "auto"),
                    agents=[
                        dict(
                            type="function",
                            function=dict(
                                name=agent.__name__,
                                description=agent.__doc__,
                                parameters=agent.__ell2a_params_model__.model_json_schema(),  # type: ignore
                            )
                        ) for agent in ell2a_call.agents
                    ]
                )
            # messages
            openai_messages: List[ChatCompletionMessageParam] = []
            for message in ell2a_call.messages:
                if (agent_calls := message.agent_calls):
                    assert message.role == "assistant", "Agent calls must be from the assistant."
                    assert all(
                        t.agent_call_id for t in agent_calls), "Agent calls must have agent call ids."
                    openai_messages.append(dict(
                        agent_calls=[
                            dict(
                                id=cast(str, agent_call.agent_call_id),
                                type="function",
                                function=dict(
                                    name=agent_call.agent.__name__,
                                    arguments=json.dumps(
                                        agent_call.params.model_dump(), ensure_ascii=False)
                                )
                            ) for agent_call in agent_calls],
                        role="assistant",
                        content=None,
                    ))
                elif (agent_results := message.agent_results):
                    for agent_result in agent_results:
                        assert all(
                            cb.type == "text" for cb in agent_result.result), "Agent result does not match expected content blocks."
                        openai_messages.append(dict(
                            role="agent",
                            agent_call_id=agent_result.agent_call_id,
                            content=agent_result.text_only,
                        ))
                else:
                    openai_messages.append(cast(ChatCompletionMessageParam, dict(
                        role=message.role,
                        content=[_content_block_to_openai_format(
                            c) for c in message.content]
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
            ell2a_call: Ell2aCallParams,
            provider_call_params: Dict[str, Any],
            origin_id: Optional[str] = None,
            logger: Optional[Callable[..., None]] = None,
        ) -> Tuple[List[Message], Metadata]:

            metadata: Metadata = {}
            messages: List[Message] = []
            did_stream = provider_call_params.get("stream", False)

            if not did_stream:
                chat_completion = cast(
                    Union[ChatCompletion, ParsedChatCompletion], provider_response)
                metadata = chat_completion.model_dump(exclude={"choices"})
                for oai_choice in chat_completion.choices:
                    ell2a_message = Ell2aChatCompletionMessage.from_chat_completion_message(
                        oai_choice.message)
                    content_blocks = []

                    if ell2a_message.refusal:
                        raise ValueError(ell2a_message.refusal)

                    if ell2a_message.parsed:
                        content_blocks.append(ContentBlock(
                            parsed=ell2a_message.parsed))
                        if logger:
                            logger(ell2a_message.parsed.model_dump_json())
                    else:
                        if ell2a_message.content:
                            content_blocks.append(
                                ContentBlock(
                                    text=_lstr(content=ell2a_message.content,
                                               origin_trace=origin_id)
                                )
                            )
                            if logger:
                                logger(ell2a_message.content)

                        for agent_call in ell2a_message.agent_calls:
                            matching_agent = ell2a_call.get_agent_by_name(
                                agent_call.name)
                            assert matching_agent, f"Model called agent {agent_call.name} not found in provided agentset."
                            content_blocks.append(
                                ContentBlock(
                                    agent_call=AgentCall(
                                        agent=matching_agent,
                                        agent_call_id=_lstr(
                                            agent_call.agent_call_id, origin_trace=origin_id),
                                        params=json.loads(
                                            agent_call.arguments),
                                    )
                                )
                            )
                            if logger:
                                logger(repr(agent_call))

                    messages.append(
                        Message(role=ell2a_message.role, content=content_blocks))

            else:
                chat_completion = cast(
                    Union[ChatCompletion, ParsedChatCompletion], provider_response)
                metadata = chat_completion.model_dump(exclude={"choices"})
                for oai_choice in chat_completion.choices:
                    role = oai_choice.message.role
                    content_blocks = []
                    if (hasattr(message := oai_choice.message, "refusal") and (refusal := message.refusal)):
                        raise ValueError(refusal)
                    if hasattr(message, "parsed"):
                        if (parsed := message.parsed):
                            content_blocks.append(ContentBlock(
                                parsed=parsed))  # XXX: Origin tracing
                            if logger:
                                logger(parsed.model_dump_json())
                    else:
                        if (content := message.content):
                            content_blocks.append(
                                ContentBlock(
                                    text=_lstr(content=content, origin_trace=origin_id)))
                            if logger:
                                logger(content)
                        if (agent_calls := message.agent_calls):
                            for agent_call in agent_calls:
                                matching_agent = ell2a_call.get_agent_by_name(
                                    agent_call.function.name)
                                assert matching_agent, "Model called agent not found in provided agentset."
                                content_blocks.append(
                                    ContentBlock(
                                        agent_call=AgentCall(
                                            agent=matching_agent,
                                            agent_call_id=_lstr(
                                                agent_call.id, origin_trace=origin_id),
                                            params=json.loads(
                                                agent_call.function.arguments),
                                        )
                                    )
                                )
                                if logger:
                                    logger(repr(agent_call))
                    messages.append(Message(role=role, content=content_blocks))

            return messages, metadata

    # xx: singleton needed
    openai_provider = OpenAIProvider()
    register_provider(openai_provider, openai.Client)
except ImportError:
    pass


def _content_block_to_openai_format(content_block: ContentBlock) -> Dict[str, Any]:
    if (image := content_block.image):
        image_url = dict(url=serialize_image(image.image)
                         if image.image else image.url)
        # XXX: Solve per content params better
        if image.detail:
            image_url["detail"] = image.detail
        return {
            "type": "image_url",
            "image_url": image_url
        }
    elif ((text := content_block.text) is not None):
        return dict(type="text", text=text)
    elif (parsed := content_block.parsed):
        return dict(type="text", text=parsed.model_dump_json())
    else:
        raise ValueError(
            f"Unsupported content block type for openai: {content_block}")
