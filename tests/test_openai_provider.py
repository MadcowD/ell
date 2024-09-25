import json
from typing import Dict
import pydantic
import pytest
from unittest.mock import MagicMock, patch
from ell.providers.openai import OpenAIProvider, _content_block_to_openai_format
from ell.provider import EllCallParams
from ell.types import Message, ContentBlock, ToolCall, ToolResult
from openai import Client
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ParsedChatCompletion,
    ChatCompletionChunk,
)
from openai._streaming import Stream



@pytest.fixture
def provider():
    return OpenAIProvider()


@pytest.fixture
def ell_call_params(openai_client):
    return EllCallParams(
        client=openai_client,  # Added the required 'client' field
        api_params={},
        model="gpt-4",
        messages=[],
        tools=[],
    )


@pytest.fixture
def openai_client():
    client = MagicMock(spec=Client)

    # Configure 'beta.chat.completions.parse'
    client.beta = MagicMock()
    client.beta.chat = MagicMock()
    client.beta.chat.completions = MagicMock()
    client.beta.chat.completions.parse = MagicMock()

    # Configure 'chat.completions.create'
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = MagicMock()

    return client


@pytest.fixture
def mock_tool():
    mock = MagicMock()
    mock.__name__ = "mock_tool"
    mock.__doc__ = "A mock tool"
    # Define the __ell_params_model__ attribute with a mock
    params_model = pydantic.create_model("MyModel", param1=(str, "..."))
    mock.__ell_params_model__ = params_model
    return mock


class TestOpenAIProvider:
    def test_provider_call_function_with_response_format(
        self, provider, openai_client, ell_call_params
    ):
        class MyModel(pydantic.BaseModel):
            pass
        api_call_params = {"response_format": MyModel}
        func = provider.provider_call_function(openai_client, api_call_params)
        assert func == openai_client.beta.chat.completions.parse

        api_call_params = {"response_format": {"type": "json_schema", "schema": {}}}
        func = provider.provider_call_function(openai_client, api_call_params)
        assert func == openai_client.chat.completions.create

    def test_provider_call_function_without_response_format(
        self, provider, openai_client, ell_call_params
    ):
        api_call_params = {}
        func = provider.provider_call_function(openai_client, api_call_params)
        assert func == openai_client.chat.completions.create

    def test_translate_to_provider_streaming_enabled(self, provider, ell_call_params):
        ell_call_params.api_params = {"some_param": "value"}
        ell_call_params.tools = []
        ell_call_params.messages = [
            Message(role="user", content=[ContentBlock(text="Hello")])
        ]

        translated = provider.translate_to_provider(ell_call_params)
        assert translated["model"] == "gpt-4"
        assert translated["stream"] is True
        assert translated["stream_options"] == {"include_usage": True}
        assert translated["messages"] == [
            {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
        ]
    def test_translate_to_provider_unregistered_model(self, provider, ell_call_params):
        """
        Test that translate_to_provider does not fail when the model is not registered.
        It should retain default streaming parameters.
        """
        # Set up the EllCallParams with a model that is not registered
        ell_call_params.model = "unregistered-model"
        ell_call_params.api_params = {} # No response_format
        ell_call_params.tools = [] # No tools
        # Perform the translation
        translated = provider.translate_to_provider(ell_call_params)
        # Assert that 'stream' and 'stream_options' are retained
        assert translated.get("stream") is True, "'stream' should be set to True by default."
        assert translated.get("stream_options") == {"include_usage": True}, (
        "'stream_options' should include 'include_usage': True by default."
        )
        # Optional: Assert that the model is correctly set
        assert translated.get("model") == "unregistered-model", "Model should be set correctly."
        # Ensure no unexpected keys are removed
        assert "stream" in translated
        assert "stream_options" in translated

    def test_translate_to_provider_streaming_disabled_due_to_response_format(
        self, provider, ell_call_params
    ):
        ell_call_params.api_params = {"response_format": "parsed"}
        ell_call_params.tools = []
        ell_call_params.messages = [
            Message(role="user", content=[ContentBlock(text="Hello")])
        ]

        translated = provider.translate_to_provider(ell_call_params)
        assert "stream" not in translated
        assert "stream_options" not in translated

    def test_translate_to_provider_with_tools(
        self, provider, ell_call_params, mock_tool
    ):
        ell_call_params.tools = [mock_tool]
        ell_call_params.api_params = {}
        ell_call_params.messages = []

        translated = provider.translate_to_provider(ell_call_params)
        assert translated["tool_choice"] == "auto"
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

    def test_translate_to_provider_with_empty_text(self, provider, ell_call_params):
        ell_call_params.messages = [
            Message(role="user", content=[ContentBlock(text="")])
        ]
        ell_call_params.tools = []
        ell_call_params.api_params = {}

        translated = provider.translate_to_provider(ell_call_params)
        
        assert translated["messages"] == [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "",
                    }
                ],
            }
        ]
        assert "tools" not in translated
        assert "tool_choice" not in translated


    def test_translate_to_provider_with_tool_calls(
        self, provider, ell_call_params, mock_tool
    ):
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

    def test_translate_to_provider_with_multiple_tool_calls(
        self, provider, ell_call_params, mock_tool
    ):
        tool_result_1 = ToolResult(
            tool_call_id="123",
            result=[ContentBlock(text="Hello World 1")]
        )
        tool_result_2 = ToolResult(
            tool_call_id="456",
            result=[ContentBlock(text="Hello World 2")]
        )
        message = Message(role="tool", content=[tool_result_1, tool_result_2])
        ell_call_params.messages = [message]
        translated = provider.translate_to_provider(ell_call_params)
        assert translated["messages"] == [
            {
                "content": "Hello World 1",
                "role": "tool",
                "tool_call_id": "123"
            },
            {
                "content": "Hello World 2",
                "role": "tool",
                "tool_call_id": "456"
            }
        ]

    def test_translate_to_provider_with_list_tool_response(
        self, provider, ell_call_params, mock_tool
    ):
        choices = [
            "Banana",
            "Apple",
            "Orange"
        ]
        tool_result = ToolResult(
            tool_call_id="123",
            result=[ContentBlock(text=choice) for choice in choices]
        )
        message = Message(role="tool", tool_result=tool_result)
        ell_call_params.messages = [message]
        translated = provider.translate_to_provider(ell_call_params)
        assert translated["messages"] == [
            {
                "content": "Banana\nApple\nOrange",
                "role": "tool",
                "tool_call_id": "123"
            },
        ]


    def test_translate_from_provider_streaming(
        self, provider, ell_call_params, openai_client
    ):
        provider_call_params = {"stream": True}
        stream_chunk = ChatCompletionChunk(
            id="chatcmpl-123",
            model="gpt-4",
            choices=[
                dict(
                    index=0,
                    delta=dict(role="assistant", content="Hello"),
                )
            ],
            created=1234567890,
            object="chat.completion.chunk",
            usage=None,
        )
        mock_stream = MagicMock(spec=Stream)
        mock_stream.__iter__.return_value = [stream_chunk]

        with patch("ell.providers.openai.Stream", return_value=mock_stream):
            messages, metadata = provider.translate_from_provider(
                provider_response=mock_stream,
                ell_call=ell_call_params,
                provider_call_params=provider_call_params,
            )
            assert messages == [
                Message(role="assistant", content=[ContentBlock(text="Hello")])
            ]
            assert metadata['id'] == 'chatcmpl-123'
            assert not metadata['usage']
            assert metadata['model'] == 'gpt-4'
            assert metadata['object'] == 'chat.completion.chunk'

    def test_translate_from_provider_non_streaming(self, provider, ell_call_params):
        provider_call_params = {"stream": False}
        chat_completion = ChatCompletion(
            id="chatcmpl-123",
            model="gpt-4",
            choices=[
                dict(
                    index=0,
                    message=dict(role="assistant", content="Hello"),
                    finish_reason="stop",
                )
            ],
            created=1234567890,
            object="chat.completion",
        )

        messages, metadata = provider.translate_from_provider(
            provider_response=chat_completion,
            ell_call=ell_call_params,
            provider_call_params=provider_call_params,
        )
        assert messages == [
            Message(role="assistant", content=[ContentBlock(text="Hello")])
        ]

    def test_translate_from_provider_with_refusal(self, provider, ell_call_params):
        chat_completion = ChatCompletion(
            id="chatcmpl-123",
            model="gpt-4",
            choices=[
                dict(
                    index=0,
                    message=dict(
                        role="assistant", content=None, refusal="Refusal message"
                    ),
                    finish_reason="stop",
                )
            ],
            created=1234567890,
            object="chat.completion",
        )

        with pytest.raises(ValueError) as excinfo:
            provider.translate_from_provider(
                provider_response=chat_completion,
                ell_call=ell_call_params,
                provider_call_params={"stream": False},
            )
        assert "Refusal message" in str(excinfo.value)

        # Additional assertions to improve test coverage
        assert excinfo.value.args[0] == "Refusal message"
        assert ell_call_params.client.mock_calls == []  # Ensure no client calls were made

    def test_translate_to_provider_with_multiple_messages(
        self, provider, ell_call_params
    ):
        ell_call_params.messages = [
            Message(role="user", content=[ContentBlock(text="Hello")]),
            Message(role="assistant", content=[ContentBlock(text="Hi there!")]),
        ]

        translated = provider.translate_to_provider(ell_call_params)
        assert translated["messages"] == [
            {"role": "user", "content": [{"type": "text", "text": "Hello"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "Hi there!"}]},
        ]

    def test_translate_to_provider(self, provider, ell_call_params):
        import numpy as np

        image_block = ContentBlock(
            image=np.random.rand(100, 100, 3), image_detail="detail"
        )  # Truncated valid base64
        openai_format = _content_block_to_openai_format(image_block)
        assert isinstance(openai_format, dict)
        assert "type" in openai_format
        assert openai_format["type"] == "image_url"
        assert "image_url" in openai_format
        assert isinstance(openai_format["image_url"], dict)
        assert "url" in openai_format["image_url"]
        assert isinstance(openai_format["image_url"]["url"], str)
        assert openai_format["image_url"]["url"].startswith("data:image/png;base64,")
        assert "detail" in openai_format["image_url"]
        assert openai_format["image_url"]["detail"] == "detail"

    def test_translate_to_provider_with_parsed_message(self, provider, ell_call_params):
        model = pydantic.create_model("MyModel", field=(str, "..."))
        parsed_block = ContentBlock(parsed=model(field="value"))
        ell_call_params.messages = [Message(role="user", content=[parsed_block])]

        translated = provider.translate_to_provider(ell_call_params)
        assert translated["messages"] == [
            {"role": "user", "content": [{"type": "text", "text": '{"field":"value"}'}]}
        ]

    def test_translate_from_provider_with_usage_metadata(
        self, provider, ell_call_params
    ):
        chunk_with_usage = ChatCompletionChunk(
            id="chunk_123",
            created=1612288000,
            object="chat.completion.chunk",
            model="gpt-4",
            choices=[
                dict(
                    index=0, delta=dict(role="assistant", content="Hello")
                )  # Added index=0
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        mock_stream = MagicMock(spec=Stream)
        mock_stream.__iter__.return_value = [chunk_with_usage]

        messages, metadata = provider.translate_from_provider(
            provider_response=mock_stream,
            ell_call=ell_call_params,
            provider_call_params={"stream": True},
        )
        assert messages == [
            Message(role="assistant", content=[ContentBlock(text="Hello")])
        ]
        assert (
            "prompt_tokens" in metadata["usage"]
            and metadata["usage"]["prompt_tokens"] == 10
        )
        assert (
            "completion_tokens" in metadata["usage"]
            and metadata["usage"]["completion_tokens"] == 5
        )
        assert (
            "total_tokens" in metadata["usage"]
            and metadata["usage"]["total_tokens"] == 15
        )

    def test_translate_from_provider_with_multiple_chunks(
        self, provider, ell_call_params
    ):
        chunk1 = ChatCompletionChunk(
            id="chunk_1",
            object="chat.completion.chunk",
            created=1234567890,
            model="gpt-4",
            choices=[dict(index=0, delta=dict(role="assistant", content="Hello"))],
        )
        chunk2 = ChatCompletionChunk(
            id="chunk_2",
            object="chat.completion.chunk",
            created=1234567891,
            model="gpt-4",
            choices=[dict(index=0, delta=dict(content=" World"))],
        )
        mock_stream = MagicMock(spec=Stream)
        mock_stream.__iter__.return_value = [chunk1, chunk2]

        messages, metadata = provider.translate_from_provider(
            provider_response=mock_stream,
            ell_call=ell_call_params,
            provider_call_params={"stream": True},
        )
        assert messages == [
            Message(role="assistant", content=[ContentBlock(text="Hello World")])
        ]


    # Suggested Test for _content_block_to_openai_format
def test_content_block_to_openai_format():
    from ell.providers.openai import _content_block_to_openai_format
    from ell.types import ContentBlock
    from ell.util.serialization import serialize_image
    from PIL import Image
    from ell.types.message import ImageContent 
    import numpy as np

    # Test text content
    text_block = ContentBlock(text="Hello World")
    expected_text = {"type": "text", "text": "Hello World"}
    assert _content_block_to_openai_format(text_block) == expected_text

    # Test parsed content
    class ParsedModel(pydantic.BaseModel):
        field: str

    parsed_block = ContentBlock(parsed=ParsedModel(field="value"))
    expected_parsed = {"type": "text", "text": '{"field":"value"}'}
    assert _content_block_to_openai_format(parsed_block) == expected_parsed

    # Test image content with image_detail
    img = Image.new('RGB', (100, 100))
    serialized_img = serialize_image(img)
    image_block = ContentBlock(image=ImageContent(image=img, detail="Sample Image"))
    expected_image = {
        "type": "image_url",
        "image_url": {
            "url": serialized_img,
            "detail": "Sample Image"
        }
    }
    assert _content_block_to_openai_format(image_block) == expected_image

    # Test image content without image_detail
    image_block_no_detail = ContentBlock(image=img)
    expected_image_no_detail = {
        "type": "image_url",
        "image_url": {
            "url": serialized_img
        }
    }
    assert _content_block_to_openai_format(image_block_no_detail) == expected_image_no_detail

    # Test unsupported content type
    with pytest.raises(ValueError):
        _content_block_to_openai_format(ContentBlock(audio=[0.1, 0.2]))

def test_translate_to_provider_no_tools_no_streaming():

    provider = OpenAIProvider()
    ell_call_params = EllCallParams(
        client=MagicMock(),
        api_params={"response_format": "parsed"},
        model="gpt-4",
        messages=[Message(role="user", content=[ContentBlock(text="Hello")])],
        tools=[]
    )

    translated = provider.translate_to_provider(ell_call_params)
    assert "stream" not in translated
    assert "stream_options" not in translated
    assert translated["response_format"] == "parsed"
    assert translated["model"] == "gpt-4"

def test_translate_to_provider_with_custom_stream_options():
    provider = OpenAIProvider()
    ell_call_params = EllCallParams(
        client=MagicMock(),
        api_params={"custom_option": True},
        model="gpt-4",
        messages=[Message(role="user", content=[ContentBlock(text="Hello")])],
        tools=[]
    )

    translated = provider.translate_to_provider(ell_call_params)
    assert translated["custom_option"] is True
    assert translated["stream"] is True
    assert translated["stream_options"] == {"include_usage": True}