
from typing import Dict

from ell.types.message import ContentBlock, ToolResult


def test_tool_json_dumping_behavior():
    from ell import tool
    import json

    # Create a mock tool function
    @tool(exempt_from_tracking=False)
    def mock_tool_function(data : Dict[str, str]):
        return data

    # Test case where result is a string and _invocation_origin is provided
    # with patch('json.dumps') as mock_json_dumps:
    result= mock_tool_function(
        # _invocation_origin="test_origin",
        _tool_call_id="tool_123",
        data={"key": "value"}
    )
    # Expect json.dumps to be called since result is a string and _invocation_origin is provided
    # mock_json_dumps.assert_called_once_with({"key": "value"})
    assert isinstance(result, ToolResult)
    assert result.tool_call_id == "tool_123"
    assert result.result == [ContentBlock(text=json.dumps({"key": "value"}))]
    # Test case where _invocation_origin is not provided
    @tool(exempt_from_tracking=False)
    def mock_tool_no_origin():
        return "Simple string result"

    result = mock_tool_no_origin(
        _tool_call_id="tool_789",
    )
    assert isinstance(result, ToolResult)
    assert result.tool_call_id == "tool_789"
    # XXX: We will json dump for now.
    assert result.result == [ContentBlock(text=json.dumps("Simple string result"))]

    # Test case where result is a list of ContentBlocks
    @tool(exempt_from_tracking=False)
    def mock_tool_content_blocks():
        return [ContentBlock(text="Block 1"), ContentBlock(text="Block 2")]

    result = mock_tool_content_blocks(
        _tool_call_id="tool_101",
    )
    # Expect json.dumps not to be called since result is already a list of ContentBlocks

    assert isinstance(result, ToolResult)
    assert result.tool_call_id == "tool_101"
    assert result.result == [ContentBlock(text="Block 1"), ContentBlock(text="Block 2")]