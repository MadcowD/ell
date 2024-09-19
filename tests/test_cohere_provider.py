import pytest
from unittest.mock import Mock
from ell.provider import APICallResult
from ell.providers.cohere import CohereProvider
from ell.types import Message, ContentBlock
from pydantic import BaseModel

@pytest.fixture
def mock_cohere_client():
    return Mock()

class DummyParams(BaseModel):
    param1: str
    param2: int

def test_content_block_to_cohere_format():
    text_block = ContentBlock(text="Hello, world!")
    assert CohereProvider.content_block_to_cohere_format(text_block) == "Hello, world!"

    class DummyParsed(BaseModel):
        field: str
    parsed_block = ContentBlock(parsed=DummyParsed(field="value"))
    
    result = CohereProvider.content_block_to_cohere_format(parsed_block)
    assert result == '{"field":"value"}'

def test_message_to_cohere_format():
    message = Message(role="user", content=[ContentBlock(text="Hello"), ContentBlock(text="world!")])
    assert CohereProvider.message_to_cohere_format(message) == {
        "role": "user",
        "message": "Hello world!"
    }

def test_call_model(mock_cohere_client):
    messages = [
        Message(role="user", content=[ContentBlock(text="Hello")]),
        Message(role="assistant", content=[ContentBlock(text="Hi there!")]),
        Message(role="user", content=[ContentBlock(text="How are you?")])
    ]
    api_params = {"temperature": 0.7, "max_tokens": 100}

    mock_cohere_client.chat.return_value = Mock(text="I'm doing well, thank you!")

    result = CohereProvider.call_model(mock_cohere_client, "command", messages, api_params)

    assert isinstance(result, APICallResult)
    assert result.actual_streaming == False
    assert result.actual_n == 1
    assert "message" in result.final_call_params
    assert result.final_call_params["model"] == "command"
    assert result.final_call_params["temperature"] == 0.7
    assert result.final_call_params["max_tokens"] == 100
    assert result.final_call_params["chat_history"] == [
        {"role": "user", "message": "Hello"},
        {"role": "assistant", "message": "Hi there!"}
    ]
    assert result.final_call_params["message"] == "How are you?"

def test_process_response():
    mock_response = Mock(text="I'm doing well, thank you!", meta=Mock(tokens=Mock(input_tokens=10, output_tokens=5)))
    call_result = APICallResult(
        response=mock_response,
        actual_streaming=False,
        actual_n=1,
        final_call_params={}
    )

    processed_messages, metadata = CohereProvider.process_response(call_result, "test_origin")

    assert len(processed_messages) == 1
    assert processed_messages[0].role == "assistant"
    assert len(processed_messages[0].content) == 1
    assert processed_messages[0].content[0].text == "I'm doing well, thank you!"
    assert metadata["usage"] == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

def test_supports_streaming():
    assert CohereProvider.supports_streaming() == False