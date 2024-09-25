import pytest
from pydantic import BaseModel
import ell
from src.ell.types.message import ContentBlock, ToolCall, ToolResult, Message
import numpy as np
from PIL import Image

class DummyParams(BaseModel):
    param1: str
    param2: int

class DummyFormattedResponse(BaseModel):
    field1: str
    field2: int

# Define a dummy callable function to use as a tool
def dummy_tool(param1: str, param2: int):
    return f"Dummy tool called with {param1} and {param2}"

def test_content_block_coerce_string():
    content = "Hello, world!"
    result = ContentBlock.coerce(content)
    assert isinstance(result, ContentBlock)
    assert result.text == content
    assert result.type == "text"

def test_content_block_coerce_tool_call():
    tool_call = ToolCall(tool=dummy_tool, params=DummyParams(param1="test", param2=42))
    result = ContentBlock.coerce(tool_call)
    assert isinstance(result, ContentBlock)
    assert result.tool_call == tool_call
    assert result.type == "tool_call"

def test_content_block_coerce_tool_result():
    tool_result = ToolResult(tool_call_id="123", result=[ContentBlock(text="Tool result")])
    result = ContentBlock.coerce(tool_result)
    assert isinstance(result, ContentBlock)
    assert result.tool_result == tool_result
    assert result.type == "tool_result"

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

    msg = Message(role="user", content=[ContentBlock(parsed=DummyFormattedResponse(field1="test", field2=42))])
    assert msg.model_dump(exclude_none=True, exclude_unset=True) == {'role': 'user', 'content': [{'parsed': {'field1': 'test', 'field2': 42}}]}


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
        ToolCall(tool=dummy_tool, params=DummyParams(param1="test", param2=42)),
        ToolResult(tool_call_id="123", result=[ContentBlock(text="Tool result")]),
        DummyFormattedResponse(field1="test", field2=42),
        ContentBlock(text="Existing content block")
    ]
    message = Message(role="user", content=content)
    
    assert len(message.content) == 5
    assert isinstance(message.content[0], ContentBlock) and message.content[0].text == "Text message"
    assert isinstance(message.content[1], ContentBlock) and isinstance(message.content[1].tool_call, ToolCall)
    assert isinstance(message.content[2], ContentBlock) and isinstance(message.content[2].tool_result, ToolResult)
    assert isinstance(message.content[3], ContentBlock) and isinstance(message.content[3].parsed, DummyFormattedResponse)
    assert isinstance(message.content[4], ContentBlock) and message.content[4].text == "Existing content block"

def test_content_block_single_non_null():
    # Valid cases
    ContentBlock.model_validate(ContentBlock(text="Hello"))
    # ContentBlock.model_validate(ContentBlock(image="image.jpg"))
    # ContentBlock.model_validate(ContentBlock(audio="audio.mp3"))
    ContentBlock.model_validate(ContentBlock(tool_call=ToolCall(tool=dummy_tool, 
                                    params=DummyParams(param1="test", param2=42))))
    ContentBlock.model_validate(ContentBlock(parsed=DummyFormattedResponse(field1="test", field2=42)))
    ContentBlock.model_validate(ContentBlock(tool_result=ToolResult(tool_call_id="123", result=[ContentBlock(text="Tool result")])))

    # New valid cases for image and audio
    dummy_image = Image.new('RGB', (100, 100))
    dummy_audio = np.array([0.1, 0.2, 0.3])

    ContentBlock.model_validate(ContentBlock(image=dummy_image))
    ContentBlock.model_validate(ContentBlock(audio=dummy_audio))

    # Invalid cases
    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(text="Hello", image="image.jpg"))
    
    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(text="Hello", tool_call=ToolCall(tool=dummy_tool, 
                                                      params=DummyParams(param1="test", param2=42))))
    
    with pytest.raises(ValueError):
        ContentBlock.model_validate(ContentBlock(image="image.jpg", audio="audio.mp3", parsed=DummyFormattedResponse(field1="test", field2=42)))

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