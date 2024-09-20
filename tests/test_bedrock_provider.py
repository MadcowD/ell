import pytest
from unittest.mock import Mock, patch
from ell.provider import APICallResult
from ell.providers.bedrock import BedrockProvider, message_to_bedrock_message_format
from ell.types import Message, ContentBlock, ToolCall
from ell.types.message import LMP, ToolResult
from pydantic import BaseModel
import json
import ell
class DummyParams(BaseModel):
    param1: str
    param2: int

@pytest.fixture
def mock_bedrock_client():
    return Mock()
import boto3


def test_supports_streaming():
    assert BedrockProvider.supports_streaming() == True

def test_message_to_bedrock_message_format():
    message_user = Message(
        role="user",
        content=[
            ContentBlock(
                type="text",
                text="Hello, world!"
            )
        ]
    )
    expected_user = [
        {
            'role':'user',
            'content':[
                {
                    'type':'text',
                    'text':'Hello, world!'
                }
            ]
        }
    ]
    message_to_bedrock_message_format(message_user) == expected_user

    message_user = Message(
        role="assistant",
        content=[
            ContentBlock(
                type="text",
                text="Hello, world!"
            )
        ]
    )
    expected_user = [
        {
            'role':'assistant',
            'content':[
                {
                    'type':'text',
                    'text':'Hello, world!'
                }
            ]
        }
    ]
    message_to_bedrock_message_format(message_user) == expected_user