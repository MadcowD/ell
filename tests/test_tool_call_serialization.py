import pytest

# must be imported from classpath, not src.., to match Pydantic type FQNs
from ell.types import ContentBlock, ToolCall, Message 
from src.ell.lmp.tool import tool

@pytest.mark.skip('helper @tool()-wrapped function, not an actual test')
@tool()
def test_tool() -> ContentBlock:
    return ContentBlock(text="success!")

def test_tool_call_json_serialization():
    original_message = Message(role='assistant', content=[ToolCall(test_tool, params={}, tool_call_id="a")])
    message_json = original_message.model_dump_json()

    loaded_message = Message.model_validate_json(message_json)

    tool_result = loaded_message.call_tools_and_collect_as_message()
    assert tool_result.content[0].tool_result.text == "success!"
