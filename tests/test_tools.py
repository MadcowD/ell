
from typing import Dict

from ell2a.types.message import ContentBlock, AgentResult


def test_agent_json_dumping_behavior():
    from ell2a import agent
    import json

    # Create a mock agent function
    @agent(exempt_from_tracking=False)
    def mock_agent_function(data: Dict[str, str]):
        return data

    # Test case where result is a string and _invocation_origin is provided
    # with patch('json.dumps') as mock_json_dumps:
    result = mock_agent_function(
        # _invocation_origin="test_origin",
        _agent_call_id="agent_123",
        data={"key": "value"}
    )
    # Expect json.dumps to be called since result is a string and _invocation_origin is provided
    # mock_json_dumps.assert_called_once_with({"key": "value"})
    assert isinstance(result, AgentResult)
    assert result.agent_call_id == "agent_123"
    assert result.result == [ContentBlock(text=json.dumps({"key": "value"}))]
    # Test case where _invocation_origin is not provided

    @agent(exempt_from_tracking=False)
    def mock_agent_no_origin():
        return "Simple string result"

    result = mock_agent_no_origin(
        _agent_call_id="agent_789",
    )
    assert isinstance(result, AgentResult)
    assert result.agent_call_id == "agent_789"
    # XXX: We will json dump for now.
    assert result.result == [ContentBlock(
        text=json.dumps("Simple string result"))]

    # Test case where result is a list of ContentBlocks
    @agent(exempt_from_tracking=False)
    def mock_agent_content_blocks():
        return [ContentBlock(text="Block 1"), ContentBlock(text="Block 2")]

    result = mock_agent_content_blocks(
        _agent_call_id="agent_101",
    )
    # Expect json.dumps not to be called since result is already a list of ContentBlocks

    assert isinstance(result, AgentResult)
    assert result.agent_call_id == "agent_101"
    assert result.result == [ContentBlock(
        text="Block 1"), ContentBlock(text="Block 2")]
