import pytest
from pydantic import BaseModel
import ell2a
from src.ell2a.types.message import ContentBlock, AgentCall, AgentResult, Message
import numpy as np
from PIL import Image


class DummyParams(BaseModel):
    param1: str
    param2: int


class DummyFormattedResponse(BaseModel):
    field1: str
    field2: int

# Define a dummy callable function to use as a agent


def dummy_agent(param1: str, param2: int):
    return f"Dummy agent called with {param1} and {param2}"


def test_content_block_coerce_string():
    content = "Hello, world!"
    result = ContentBlock.coerce(content)
    assert isinstance(result, ContentBlock)
    assert result.text == content
    assert result.type == "text"


def test_content_block_coerce_agent_call():
    agent_call = AgentCall(
        agent=dummy_agent, params=DummyParams(param1="test", param2=42))
    result = ContentBlock.coerce(agent_call)
    assert isinstance(result, ContentBlock)
    assert result.agent_call == agent_call
    assert result.type == "agent_call"


def test_content_block_coerce_agent_result():
    agent_result = AgentResult(agent_call_id="123", result=[
                             ContentBlock(text="Agent result")])
    result = ContentBlock.coerce(agent_result)
    assert isinstance(result, ContentBlock)
    assert result.agent_result == agent_result
    assert result.type == "agent_result"


def test_content_block_coerce_base_model():
    formatted_response = DummyFormattedResponse(field1="test", field2=42)
    result = ContentBlock.coerce(formatted_response)
    assert isinstance(result, ContentBlock)
    assert result.parsed == formatted_response
    assert result.type == "parsed"


def test_serialization_of_content_block_with_parsed():
    class DummyFormattedResponse(BaseModel):
        field1: str
        field2: int

    msg = Message(role="user", content=[ContentBlock(
        parsed=DummyFormattedResponse(field1="test", field2=42))])
    assert msg.model_dump(exclude_none=True, exclude_unset=True) == {
        'role': 'user', 'content': [{'parsed': {'field1': 'test', 'field2': 42}}]}


def test_content_block_coerce_content_block():
    original_block = ContentBlock(text="Original content")
    result = ContentBlock.coerce(original_block)
    assert result is original_block  # Should return the same object


def test_content_block_coerce_invalid_type():
    with pytest.raises(ValueError):
        ContentBlock.coerce(123)  # Integer is not a valid type


def test_message_coercion():
    content = [
        "Text message",
        AgentCall(agent=dummy_agent, params=DummyParams(
            param1="test", param2=42)),
        AgentResult(agent_call_id="123", result=[
                   ContentBlock(text="Agent result")]),
        DummyFormattedResponse(field1="test", field2=42),
        ContentBlock(text="Existing content block")
    ]
    message = Message(role="user", content=content)

    assert len(message.content) == 5
    assert isinstance(
        message.content[0], ContentBlock) and message.content[0].text == "Text message"
    assert isinstance(message.content[1], ContentBlock) and isinstance(
        message.content[1].agent_call, AgentCall)
    assert isinstance(message.content[2], ContentBlock) and isinstance(
        message.content[2].agent_result, AgentResult)
    assert isinstance(message.content[3], ContentBlock) and isinstance(
        message.content[3].parsed, DummyFormattedResponse)
    assert isinstance(
        message.content[4], ContentBlock) and message.content[4].text == "Existing content block"


def test_content_block_single_non_null():
    # Valid cases
    ContentBlock.model_validate(ContentBlock(text="Hello"))
    # ContentBlock.model_validate(ContentBlock(image="image.jpg"))
    # ContentBlock.model_validate(ContentBlock(audio="audio.mp3"))
    ContentBlock.model_validate(ContentBlock(agent_call=AgentCall(agent=dummy_agent,
                                                                params=DummyParams(param1="test", param2=42))))
    ContentBlock.model_validate(ContentBlock(
        parsed=DummyFormattedResponse(field1="test", field2=42)))
    ContentBlock.model_validate(ContentBlock(agent_result=AgentResult(
        agent_call_id="123", result=[ContentBlock(text="Agent result")])))

    # New valid cases for image and audio
    dummy_image = Image.new('RGB', (100, 100))
    dummy_audio = np.array([0.1, 0.2, 0.3])

    ContentBlock.model_validate(ContentBlock(image=dummy_image))
    ContentBlock.model_validate(ContentBlock(audio=dummy_audio))

    # Invalid cases
    with pytest.raises(ValueError):
        ContentBlock.model_validate(
            ContentBlock(text="Hello", image="image.jpg"))

    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(text="Hello", agent_call=AgentCall(agent=dummy_agent,
                                                                                  params=DummyParams(param1="test", param2=42))))

    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(
            image="image.jpg", audio="audio.mp3", parsed=DummyFormattedResponse(field1="test", field2=42)))

    # New invalid cases for image and audio
    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(image="image.jpg"))

    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(audio="audio.mp3"))

# Add new tests for image and audio validation


def test_content_block_image_validation():
    valid_image = Image.new('RGB', (100, 100))
    invalid_image = "image.jpg"

    ContentBlock.model_validate(ContentBlock(image=valid_image))

    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(image=invalid_image))


def test_content_block_audio_validation():
    valid_audio = np.array([0.1, 0.2, 0.3])
    invalid_audio = "audio.mp3"

    ContentBlock.model_validate(ContentBlock(audio=valid_audio))

    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(audio=invalid_audio))
