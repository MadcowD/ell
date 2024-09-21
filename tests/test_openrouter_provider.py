import json
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel

import ell
from ell.models.openrouter import OpenRouter
from ell.provider import APICallResult
from ell.providers.openrouter import OpenRouterProvider
from ell.types import Message, ContentBlock, ToolCall
from ell.types.message import ToolResult


class DummyParams(BaseModel):
    param1: str
    param2: int

@pytest.fixture
def mock_openrouter_client():
    client = Mock(spec=OpenRouter, auto_spec=True)
    client.fetch_generation_data = False
    client._used_models = {}
    client.global_stats = {
        'total_cost': 0,
        'total_tokens': 0,
        'used_providers': set()
    }
    return client

def test_content_block_to_openrouter_format():
    # Test text content
    text_block = ContentBlock(text="Hello, world!")
    assert OpenRouterProvider.content_block_to_openrouter_format(text_block) == {
        "type": "text",
        "text": "Hello, world!"
    }

    # Test parsed content
    class DummyParsed(BaseModel):
        field: str
    parsed_block = ContentBlock(parsed=DummyParsed(field="value"))

    res = OpenRouterProvider.content_block_to_openrouter_format(parsed_block)
    assert res["type"] == "text"
    assert json.loads(res["text"]) == {"field": "value"}

    # Test image content (mocked)
    with patch('ell.providers.openrouter.serialize_image', return_value="base64_image_data"):
        # Test random image content
        import numpy as np
        from PIL import Image
        
        # Generate a random image
        random_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        pil_image = Image.fromarray(random_image)
        
        with patch('ell.providers.openrouter.serialize_image', return_value="random_base64_image_data"):
            random_image_block = ContentBlock(image=pil_image)
            assert OpenRouterProvider.content_block_to_openrouter_format(random_image_block) == {
                "type": "image_url",
                "image_url": {
                    "url": "random_base64_image_data"
                }
            }

def test_message_to_openrouter_format():
    # Test simple message
    simple_message = Message(role="user", content=[ContentBlock(text="Hello")])
    assert OpenRouterProvider.message_to_openrouter_format(simple_message) == {
        "role": "user",
        "content": [{"type": "text", "text": "Hello"}]
    }

    # Test message with tool calls
    def dummy_tool(param1: str, param2: int): pass
    tool_call = ToolCall(tool=dummy_tool, tool_call_id="123", params=DummyParams(param1="test", param2=42))
    tool_message = Message(role="assistant", content=[tool_call])
    formatted = OpenRouterProvider.message_to_openrouter_format(tool_message)
    assert formatted["role"] == "assistant"
    assert formatted["content"] is None
    assert len(formatted["tool_calls"]) == 1
    assert formatted["tool_calls"][0]["id"] == "123"
    assert formatted["tool_calls"][0]["type"] == "function"
    assert formatted["tool_calls"][0]["function"]["name"] == "dummy_tool"
    assert json.loads(formatted["tool_calls"][0]["function"]["arguments"]) == {"param1": "test", "param2": 42}

    # Test message with tool results
    tool_result_message = Message(
        role="user",
        content=[ToolResult(tool_call_id="123", result=[ContentBlock(text="Tool output")])],
    )
    formatted = OpenRouterProvider.message_to_openrouter_format(tool_result_message)
    assert formatted["role"] == "tool"
    assert formatted["tool_call_id"] == "123"
    assert formatted["content"] == "Tool output"

def test_call_model(mock_openrouter_client):
    messages = [Message(role="user", content=[ContentBlock(text="Hello")], refusal=None)]
    api_params = {"temperature": 0.7}

    # Mock the client's chat_completions method
    mock_openrouter_client.chat_completions.return_value = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo-0613",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I assist you today?"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    }

    @ell.tool()
    def dummy_tool(param1: str, param2: int): pass

    result = OpenRouterProvider.call_model(mock_openrouter_client, "gpt-3.5-turbo", messages, api_params, tools=[dummy_tool])

    assert isinstance(result, APICallResult)
    assert not "stream" in result.final_call_params
    assert not result.actual_streaming
    assert result.actual_n == 1
    assert "messages" in result.final_call_params
    assert result.final_call_params["model"] == "gpt-3.5-turbo"

def test_process_response():
    # Mock APICallResult
    mock_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo-0613",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello, world!"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    }
    call_result = APICallResult(
        response=mock_response,
        actual_streaming=False,
        actual_n=1,
        final_call_params={}
    )

    processed_messages, metadata = OpenRouterProvider.process_response(call_result, "test_origin")

    assert len(processed_messages) == 1
    assert processed_messages[0].role == "assistant"
    assert len(processed_messages[0].content) == 1
    assert processed_messages[0].content[0].text == "Hello, world!"
    assert metadata["id"] == "chatcmpl-123"
    assert metadata["model"] == "gpt-3.5-turbo-0613"

def test_supports_streaming():
    assert OpenRouterProvider.supports_streaming() == True
