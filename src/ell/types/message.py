# todo: implement tracing for structured outs. this a v2 feature.
from ell._lstr import _lstr


from pydantic import BaseModel, Field, model_validator
from sqlmodel import Field

from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import Any, Callable, Dict, List, Optional, Type, Union
_lstr_generic = Union[_lstr, str]
InvocableTool = Callable[..., Union["ToolResult", _lstr_generic, List["MessageContentBlock"], ]]


class ToolCall(BaseModel):
    tool : InvocableTool
    tool_call_id : Optional[str] = Field(default=None)
    params : Union[Type[BaseModel], BaseModel]
    def __call__(self, **kwargs):
        assert not kwargs, "Unexpected arguments provided. Calling a tool uses the params provided in the ToolCall."
        return self.tool(**self.params.model_dump())

    def call_and_collect_as_message_block(self):
        return ContentBlock(tool_result=ToolResult(tool_call_id=self.tool_call_id, result=self.tool(**self.params.model_dump())))

    def call_and_collect_as_message(self):
        return Message(role="user", content=[self.call_and_collect_as_message_block()])

class ToolResult(BaseModel):
    tool_call_id: str
    result: List["ContentBlock"]


class ContentBlock(BaseModel):
    text: Optional[_lstr_generic] = Field(default=None)
    image: Optional[str] = Field(default=None)
    audio: Optional[str] = Field(default=None)
    tool_call: Optional[ToolCall] = Field(default=None)
    formatted_response: Optional[Union[Type[BaseModel], BaseModel]] = Field(default=None)
    tool_result: Optional[ToolResult] = Field(default=None)

    @model_validator(mode='after')
    def check_single_non_null(self):
        non_null_fields = [field for field, value in self.__dict__.items() if value is not None]
        if len(non_null_fields) > 1:
            raise ValueError(f"Only one field can be non-null. Found: {', '.join(non_null_fields)}")
        return self

    @property
    def type(self):
        if self.text is not None:
            return "text"
        if self.image is not None:
            return "image"
        if self.audio is not None:
            return "audio"
        if self.tool_call is not None:
            return "tool_call"
        if self.formatted_response is not None:
            return "formatted_response"
        if self.tool_result is not None:
            return "tool_result"
        return None

    @classmethod
    def coerce(cls, content: Union[str, ToolCall, ToolResult, BaseModel, "ContentBlock"]) -> ["ContentBlock"]:
        if isinstance(content, ContentBlock):
            return content
        if isinstance(content, str):
            return cls(text=content)
        if isinstance(content, ToolCall):
            return cls(tool_call=content)
        if isinstance(content, ToolResult):
            return cls(tool_result=content)
        if isinstance(content, BaseModel):
            return cls(formatted_response=content)
        raise ValueError(f"Invalid content type: {type(content)}")


class Message(BaseModel):
    role: str
    content: List[ContentBlock]

    def __init__(self, role, content: Union[str, List[ContentBlock], List[Union[str, ContentBlock, ToolCall, ToolResult, BaseModel]]] = None, **content_block_kwargs):
        if not content:
            content = [ContentBlock(**content_block_kwargs)]

        if not isinstance(content, list):
            content = [content]
        
        content = [ContentBlock.model_validate(ContentBlock.coerce(c)) for c in content]
        super().__init__(content=content, role=role)

    @property
    def text(self, text_only=False) -> str:
        return "\n".join(c.text for c in self.content if c.text) if text_only else "\n".join(c.text or f"<{c.type}>" for c in self.content)

    @property
    def tool_calls(self) -> List[ToolCall]:
        return [c for c in self.content if c.tool_call is not None]
    
    @property
    def tool_results(self) -> List[ToolResult]:
        return [c for c in self.content if c.tool_result is not None]

    @property
    def formatted_responses(self) -> List[BaseModel]:
        return [c for c in self.content if c.formatted_response is not None]
    
    def call_tools_and_collect_as_message(self, parallel=False, max_workers=None):
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(c.call_and_collect_as_message_block) for c in self.tool_calls]
                content = [future.result() for future in as_completed(futures)]
        else:
            content = [c.call_and_collect_as_message_block() for c in self.tool_calls]
        return Message(role="user", content=content)

    def to_openai_message(self) -> List[Dict[str, Any]]:
        return     {
                "role": self.role,
                "content": self.text
            }
        

# HELPERS 
def system(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create a system message with the given content.

    Args:
    content (str): The content of the system message.

    Returns:
    Message: A Message object with role set to 'system' and the provided content.
    """
    return Message(role="system", content=content)


def user(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create a user message with the given content.

    Args:
    content (str): The content of the user message.

    Returns:
    Message: A Message object with role set to 'user' and the provided content.
    """
    return Message(role="user", content=content)


def assistant(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create an assistant message with the given content.

    Args:
    content (str): The content of the assistant message.

    Returns:
    Message: A Message object with role set to 'assistant' and the provided content.
    """
    return Message(role="assistant", content=content)


# want to enable a use case where the user can actually return a standrd oai chat format
# This is a placehodler will likely come back later for this
LMPParams = Dict[str, Any]
# Well this is disappointing, I wanted to effectively type hint by doign that data sync meta, but eh, at elast we can still reference role or content this way. Probably wil lcan the dict sync meta. TypedDict is the ticket ell oh ell.
MessageOrDict = Union[Message, Dict[str, str]]
# Can support iamge prompts later.
Chat = List[
    Message
]  # [{"role": "system", "content": "prompt"}, {"role": "user", "content": "message"}]
MultiTurnLMP = Callable[..., Chat]
OneTurn = Callable[..., _lstr_generic]
# This is the specific LMP that must accept history as an argument and can take any additional arguments
ChatLMP = Callable[[Chat, Any], Chat]
LMP = Union[OneTurn, MultiTurnLMP, ChatLMP]
InvocableLM = Callable[..., _lstr_generic]