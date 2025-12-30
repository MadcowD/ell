"""Tests for ToolCall serialization.

This module tests that ToolCall objects can be serialized to JSON
and deserialized back, allowing for message history persistence.

Fixes: https://github.com/MadcowD/ell/issues/412
"""

import pytest
import json

import ell
from ell.types import ContentBlock, Message
from ell.types.message import ToolCall


# Define test tools at module level for proper import resolution
@ell.tool()
def simple_test_tool(value: int) -> str:
    """A simple test tool that returns a string."""
    return f"result: {value}"


@ell.tool()
def no_param_tool() -> str:
    """A tool with no parameters."""
    return "no params result"


class TestToolCallSerialization:
    """Test ToolCall serialization and deserialization."""

    def test_tool_call_model_dump_json(self):
        """Test that ToolCall can be serialized to JSON."""
        tool_call = ToolCall(
            tool=simple_test_tool,
            params={"value": 42},
            tool_call_id="test-id-123"
        )

        # Should not raise
        json_str = tool_call.model_dump_json()

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert "tool" in data
        assert data["tool"]["module"] == "tests.test_tool_call_serialization"
        assert data["tool"]["qualname"] == "simple_test_tool"

    def test_tool_call_roundtrip(self):
        """Test that ToolCall can be serialized and deserialized."""
        original = ToolCall(
            tool=simple_test_tool,
            params={"value": 42},
            tool_call_id="test-id-123"
        )

        # Serialize
        json_str = original.model_dump_json()

        # Deserialize
        loaded = ToolCall.model_validate_json(json_str)

        # Verify the tool is callable
        assert callable(loaded.tool)
        assert loaded.tool_call_id == "test-id-123"
        assert loaded.params.value == 42

    def test_tool_call_invocation_after_deserialize(self):
        """Test that deserialized ToolCall can be invoked."""
        original = ToolCall(
            tool=simple_test_tool,
            params={"value": 99},
            tool_call_id="test-invoke-id"
        )

        # Serialize and deserialize
        json_str = original.model_dump_json()
        loaded = ToolCall.model_validate_json(json_str)

        # Invoke the tool
        result = loaded()
        assert result == "result: 99"

    def test_message_with_tool_call_serialization(self):
        """Test that Message containing ToolCall can be serialized."""
        message = Message(
            role="assistant",
            content=[
                ToolCall(
                    tool=simple_test_tool,
                    params={"value": 123},
                    tool_call_id="msg-tool-id"
                )
            ]
        )

        # Should not raise
        json_str = message.model_dump_json()

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["role"] == "assistant"
        assert len(data["content"]) == 1
        assert "tool_call" in data["content"][0]

    def test_message_with_tool_call_roundtrip(self):
        """Test that Message with ToolCall can be serialized and deserialized."""
        original_message = Message(
            role="assistant",
            content=[
                ToolCall(
                    tool=simple_test_tool,
                    params={"value": 456},
                    tool_call_id="roundtrip-id"
                )
            ]
        )

        # Serialize
        json_str = original_message.model_dump_json()

        # Deserialize
        loaded_message = Message.model_validate_json(json_str)

        # Verify
        assert loaded_message.role == "assistant"
        assert len(loaded_message.tool_calls) == 1
        assert loaded_message.tool_calls[0].tool_call_id == "roundtrip-id"
        assert callable(loaded_message.tool_calls[0].tool)

    def test_no_param_tool_serialization(self):
        """Test serialization of tool with no parameters."""
        tool_call = ToolCall(
            tool=no_param_tool,
            params={},
            tool_call_id="no-param-id"
        )

        # Serialize and deserialize
        json_str = tool_call.model_dump_json()
        loaded = ToolCall.model_validate_json(json_str)

        # Invoke
        result = loaded()
        assert result == "no params result"

    def test_invalid_tool_dict_raises_error(self):
        """Test that invalid tool dict raises appropriate error."""
        with pytest.raises(ValueError, match="Failed to resolve tool"):
            ToolCall.validate_tool({
                "module": "nonexistent.module",
                "qualname": "nonexistent_tool"
            })

    def test_tool_must_be_callable_or_dict(self):
        """Test that tool must be either callable or dict."""
        with pytest.raises(ValueError, match="Expected tool to be a callable"):
            ToolCall.validate_tool("not_a_callable_or_dict")


class TestToolCallSerializationWithCallTools:
    """Test ToolCall serialization with call_tools_and_collect_as_message."""

    def test_call_tools_after_deserialization(self):
        """Test that call_tools_and_collect_as_message works after deserialization."""
        # Create message with tool call
        original_message = Message(
            role="assistant",
            content=[
                ToolCall(
                    tool=simple_test_tool,
                    params={"value": 789},
                    tool_call_id="call-tools-test"
                )
            ]
        )

        # Serialize and deserialize
        json_str = original_message.model_dump_json()
        loaded_message = Message.model_validate_json(json_str)

        # Call tools
        result_message = loaded_message.call_tools_and_collect_as_message()

        # Verify result
        assert result_message.role == "user"
        assert len(result_message.tool_results) == 1
        # The tool result should contain our expected output
        assert "result: 789" in result_message.text
