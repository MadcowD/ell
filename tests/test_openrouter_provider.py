import pytest
import pydantic
from unittest.mock import MagicMock, patch
from ell.providers.openrouter import OpenRouterProvider
from ell.provider import EllCallParams
from ell.types import Message, ContentBlock, ToolCall
from ell.types.message import ToolResult

@pytest.fixture
def provider():
    return OpenRouterProvider()

@pytest.fixture
def ell_call_params(openrouter_client):
    return EllCallParams(
        client=openrouter_client,
        api_params={},
        model="gpt-3.5-turbo",
        messages=[],
        tools=[],
    )

@pytest.fixture
def openrouter_client():
    client = MagicMock()
    client.chat.completions.create = MagicMock()
    return client

@pytest.fixture
def mock_tool():
    mock = MagicMock()
    mock.__name__ = "mock_tool"
    mock.__doc__ = "A mock tool"
    params_model = pydantic.create_model("MyModel", param1=(str, "..."))
    mock.__ell_params_model__ = params_model
    return mock

class TestOpenRouterProvider:
    def test_translate_to_provider_streaming_enabled(self, provider, ell_call_params):
        ell_call_params.api_params = {"some_param": "value"}
        ell_call_params.messages = [
            Message(role="user", content=[ContentBlock(text="Hello")])
        ]

        translated = provider.translate_to_provider(ell_call_params)
        assert translated["model"] == "gpt-3.5-turbo"
        assert translated["messages"] == [
            {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
        ]

    def test_translate_to_provider_with_tools(self, provider, ell_call_params, mock_tool):
        ell_call_params.tools = [mock_tool]
        ell_call_params.messages = []

        translated = provider.translate_to_provider(ell_call_params)
        assert translated["tools"] == [
            {
                "type": "function",
                "function": {
                    "name": "mock_tool",
                    "description": "A mock tool",
                    "parameters": {
                        "properties": {
                            "param1": {
                                "default": "...",
                                "title": "Param1",
                                "type": "string",
                            },
                        },
                        "title": "MyModel",
                        "type": "object",
                    },
                },
            }
        ]

    def test_translate_to_provider_with_tool_calls(self, provider, ell_call_params, mock_tool):
        tool_call = ToolCall(
            tool=mock_tool, tool_call_id="123", params={"param1": "value1"}
        )
        message = Message(role="assistant", content=[tool_call])
        ell_call_params.tools = [mock_tool]
        ell_call_params.messages = [message]

        translated = provider.translate_to_provider(ell_call_params)
        assert translated["messages"] == [
            {
                "tool_calls": [
                    {
                        "id": "123",
                        "type": "function",
                        "function": {
                            "name": "mock_tool",
                            "arguments": '{"param1": "value1"}',
                        },
                    }
                ],
                "role": "assistant",
                "content": None,
            }
        ]

    def test_translate_from_provider_streaming(self, provider, ell_call_params, openrouter_client):
        provider_call_params = {"stream": True}
        stream_chunk = {
            "id": "chatcmpl-123",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": "Hello"},
                    "finish_reason": None
                }
            ]
        }
        mock_stream = MagicMock()
        mock_stream.__iter__.return_value = [stream_chunk]
        openrouter_client.chat.completions.create.return_value = mock_stream

        messages, metadata = provider.translate_from_provider(
            provider_response=mock_stream,
            ell_call=ell_call_params,
            provider_call_params=provider_call_params,
        )
        assert messages == [
            Message(role="assistant", content=[ContentBlock(text="Hello")])
        ]
        assert metadata['id'] == 'chatcmpl-123'
        assert metadata['model'] == 'gpt-3.5-turbo'
        assert metadata['object'] == 'chat.completion.chunk'

    def test_translate_from_provider_non_streaming(self, provider, ell_call_params, openrouter_client):
        provider_call_params = {"stream": False}
        chat_completion = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello"},
                    "finish_reason": "stop"
                }
            ]
        }
        openrouter_client.chat.completions.create.return_value = chat_completion

        messages, metadata = provider.translate_from_provider(
            provider_response=chat_completion,
            ell_call=ell_call_params,
            provider_call_params=provider_call_params,
        )
        assert messages == [
            Message(role="assistant", content=[ContentBlock(text="Hello")])
        ]
        assert metadata['id'] == 'chatcmpl-123'
        assert metadata['model'] == 'gpt-3.5-turbo'
        assert metadata['object'] == 'chat.completion'

    def test_translate_from_provider_with_tool_results(self, provider, ell_call_params):
        tool_result = ToolResult(tool_call_id="123", result=[ContentBlock(text="Tool output")])
        message = Message(role="tool", content=[tool_result])
        ell_call_params.messages = [message]

        translated = provider.translate_to_provider(ell_call_params)
        assert translated["messages"] == [
            {
                "role": "tool",
                "tool_call_id": "123",
                "content": "Tool output"
            }
        ]