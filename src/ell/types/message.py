# todo: implement tracing for structured outs. this a v2 feature.
import json
from ell.types._lstr import _lstr
from functools import cached_property
import numpy as np
import base64
from io import BytesIO
from PIL import Image as PILImage

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator, field_serializer
from sqlmodel import Field

from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import Any, Callable, Dict, List, Literal, Optional, Type, Union

from ell.util.serialization import serialize_image
_lstr_generic = Union[_lstr, str]
InvocableTool = Callable[..., Union["ToolResult", _lstr_generic, List["ContentBlock"], ]]




class ToolResult(BaseModel):
    tool_call_id: _lstr_generic
    result: List["ContentBlock"]

    @property
    def text(self) -> str:
        return _content_to_text(self.result)
    
    @property
    def text_only(self) -> str:
        return _content_to_text_only(self.result)
    
    # # XXX: Possibly deprecate
    # def readable_repr(self) -> str:
    #     return f"ToolResult(tool_call_id={self.tool_call_id}, result={_content_to_text(self.result)})"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(tool_call_id={self.tool_call_id}, result={_content_to_text(self.result)})"

class ToolCall(BaseModel):
    tool : InvocableTool
    tool_call_id : Optional[_lstr_generic] = Field(default=None)
    params : BaseModel

    def __init__(self, tool, params : Union[BaseModel, Dict[str, Any]],  tool_call_id=None):
        if not isinstance(params, BaseModel):
            params = tool.__ell_params_model__(**params) #convenience.
        super().__init__(tool=tool, tool_call_id=tool_call_id, params=params)

    def __call__(self, **kwargs):
        assert not kwargs, "Unexpected arguments provided. Calling a tool uses the params provided in the ToolCall."

        # XXX: TODO: MOVE TRACKING CODE TO _TRACK AND OUT OF HERE AND API.
        return self.tool(**self.params.model_dump())
    
    # XXX: Deprecate in 0.1.0
    def call_and_collect_as_message_block(self):
        raise DeprecationWarning("call_and_collect_as_message_block is deprecated. Use collect_as_content_block instead.")
    
    def call_and_collect_as_content_block(self):
        res = self.tool(**self.params.model_dump(), _tool_call_id=self.tool_call_id)
        return ContentBlock(tool_result=res)

    def call_and_collect_as_message(self):
        return Message(role="user", content=[self.call_and_collect_as_message_block()])
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.tool.__name__}({self.params}), tool_call_id='{self.tool_call_id}')"
    

class ImageContent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    image: Optional[PILImage.Image] = Field(default=None)
    url: Optional[str] = Field(default=None)
    detail: Optional[str] = Field(default=None)

    @model_validator(mode='after')
    def check_image_or_url(self):
        if self.image is not None and self.url is not None:
            raise ValueError("Both 'image' and 'url' cannot be set simultaneously.")
        if self.image is None and self.url is None:
            raise ValueError("Either 'image' or 'url' must be set.")
        return self

    @classmethod
    def coerce(cls, value: Union[str, np.ndarray, PILImage.Image, "ImageContent"]):
        if isinstance(value, cls):
            return value
        
        if isinstance(value, str):
            if value.startswith('http://') or value.startswith('https://'):
                return cls(url=value)
            try:
                img_data = base64.b64decode(value)
                img = PILImage.open(BytesIO(img_data))
                if img.mode not in ('L', 'RGB', 'RGBA'):
                    return cls(image=img.convert('RGB'))
            except:
                raise ValueError("Invalid base64 string or URL for image")
        
        if isinstance(value, np.ndarray):
            if value.ndim == 3 and value.shape[2] in (3, 4):
                mode = 'RGB' if value.shape[2] == 3 else 'RGBA'
                return cls(image=PILImage.fromarray(value, mode=mode))
            else:
                raise ValueError(f"Invalid numpy array shape for image: {value.shape}. Expected 3D array with 3 or 4 channels.")
        
        if isinstance(value, PILImage.Image):
            if value.mode not in ('L', 'RGB', 'RGBA'):
                value = value.convert('RGB')
            return cls(image=value)
        
        raise ValueError(f"Invalid image type: {type(value)}")

    @field_serializer('image')
    def serialize_image(self, image: Optional[PILImage.Image], _info):
        if image is None:
            return None
        return serialize_image(image)

class ContentBlock(BaseModel):    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    text: Optional[_lstr_generic] = Field(default=None)
    image: Optional[ImageContent] = Field(default=None)
    audio: Optional[Union[np.ndarray, List[float]]] = Field(default=None)
    tool_call: Optional[ToolCall] = Field(default=None)
    parsed: Optional[BaseModel] = Field(default=None)
    tool_result: Optional[ToolResult] = Field(default=None)
    # TODO: Add a JSON type? This would be nice for response_format. This is different than resposne_format = model. Or we could be opinionated and automatically parse the json response. That might be nice.
    # This breaks us maintaing parity with the openai python client in some sen but so does image.

    def __init__(self, *args, **kwargs):
        if "image" in kwargs and not isinstance(kwargs["image"], ImageContent):
            im = kwargs["image"] = ImageContent.coerce(kwargs["image"])
            # XXX: Backwards compatibility, Deprecate.
            if (d := kwargs.get("image_detail", None)): im.detail = d

        super().__init__(*args, **kwargs)


    @model_validator(mode='after')
    def check_single_non_null(self):
        non_null_fields = [field for field, value in self.__dict__.items() if value is not None]
        if len(non_null_fields) > 1:
            raise ValueError(f"Only one field can be non-null. Found: {', '.join(non_null_fields)}")
        return self
    
    def __str__(self):
        return repr(self)

    def __repr__(self):
        non_null_fields = [f"{field}={value}" for field, value in self.__dict__.items() if value is not None]
        return f"ContentBlock({', '.join(non_null_fields)})"

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
        if self.parsed is not None:
            return "parsed"
        if self.tool_result is not None:
            return "tool_result"
        return None
    
    @property
    def content(self):
        return getattr(self, self.type)

    @classmethod
    def coerce(cls, content: Union["ContentBlock", str, ToolCall, ToolResult, ImageContent, np.ndarray, PILImage.Image, BaseModel]) -> "ContentBlock":
        """
        Coerce various types of content into a ContentBlock.

        This method provides a flexible way to create ContentBlock instances from different types of input.

        Args:
        content: The content to be coerced into a ContentBlock. Can be one of the following types:
        - str: Will be converted to a text ContentBlock.
        - ToolCall: Will be converted to a tool_call ContentBlock.
        - ToolResult: Will be converted to a tool_result ContentBlock.
        - BaseModel: Will be converted to a parsed ContentBlock.
        - ContentBlock: Will be returned as-is.
        - Image: Will be converted to an image ContentBlock.
        - np.ndarray: Will be converted to an image ContentBlock.
        - PILImage.Image: Will be converted to an image ContentBlock.

        Returns:
        ContentBlock: A new ContentBlock instance containing the coerced content.

        Raises:
        ValueError: If the content cannot be coerced into a valid ContentBlock.

        Examples:
        >>> ContentBlock.coerce("Hello, world!")
        ContentBlock(text="Hello, world!")

        >>> tool_call = ToolCall(...)
        >>> ContentBlock.coerce(tool_call)
        ContentBlock(tool_call=tool_call)

        >>> tool_result = ToolResult(...)
        >>> ContentBlock.coerce(tool_result)
        ContentBlock(tool_result=tool_result)

        >>> class MyModel(BaseModel):
        ...     field: str
        >>> model_instance = MyModel(field="value")
        >>> ContentBlock.coerce(model_instance)
        ContentBlock(parsed=model_instance)

        >>> from PIL import Image as PILImage
        >>> img = PILImage.new('RGB', (100, 100))
        >>> ContentBlock.coerce(img)
        ContentBlock(image=ImageContent(image=<PIL.Image.Image object>))

        >>> import numpy as np
        >>> arr = np.random.rand(100, 100, 3)
        >>> ContentBlock.coerce(arr)
        ContentBlock(image=ImageContent(image=<PIL.Image.Image object>))

        >>> image = Image(url="https://example.com/image.jpg")
        >>> ContentBlock.coerce(image)
        ContentBlock(image=ImageContent(url="https://example.com/image.jpg"))

        Notes:
        - This method is particularly useful when working with heterogeneous content types
          and you want to ensure they are all properly encapsulated in ContentBlock instances.
        - The method performs type checking and appropriate conversions to ensure the resulting
          ContentBlock is valid according to the model's constraints.
        - For image content, Image objects, PIL Image objects, and numpy arrays are supported,
          with automatic conversion to the appropriate format.
        - As a last resort, the method will attempt to create an image from the input before
          raising a ValueError.
        """
        if isinstance(content, ContentBlock):
            return content
        if isinstance(content, str):
            return cls(text=content)
        if isinstance(content, ToolCall):
            return cls(tool_call=content)
        if isinstance(content, ToolResult):
            return cls(tool_result=content)
        if isinstance(content, (ImageContent, np.ndarray, PILImage.Image)):
            return cls(image=ImageContent.coerce(content))
        if isinstance(content, BaseModel):
            return cls(parsed=content)

        raise ValueError(f"Invalid content type: {type(content)}")
    
    @field_serializer('parsed')
    def serialize_parsed(self, value: Optional[BaseModel], _info):
        if value is None:
            return None
        return value.model_dump(exclude_none=True, exclude_unset=True)
    

def to_content_blocks(
    content: Optional[Union[str, List[ContentBlock], List[Union[ContentBlock, str, ToolCall, ToolResult, ImageContent, np.ndarray, PILImage.Image, BaseModel]]]] = None,
    **content_block_kwargs
) -> List[ContentBlock]:
    """
    Coerce a variety of input types into a list of ContentBlock objects.

    Args:
    content: The content to be coerced. Can be a single item or a list of items.
             Supported types include str, ContentBlock, ToolCall, ToolResult, BaseModel, Image, np.ndarray, and PILImage.Image.
    **content_block_kwargs: Additional keyword arguments to pass to ContentBlock creation if content is None.

    Returns:
    List[ContentBlock]: A list of ContentBlock objects created from the input content.

    Examples:
    >>> coerce_content_list("Hello")
    [ContentBlock(text="Hello")]

    >>> coerce_content_list([ContentBlock(text="Hello"), "World"])
    [ContentBlock(text="Hello"), ContentBlock(text="World")]

    >>> from PIL import Image as PILImage
    >>> pil_image = PILImage.new('RGB', (100, 100))
    >>> coerce_content_list(pil_image)
    [ContentBlock(image=Image(image=<PIL.Image.Image object>))]

    >>> coerce_content_list(Image(url="https://example.com/image.jpg"))
    [ContentBlock(image=Image(url="https://example.com/image.jpg"))]

    >>> coerce_content_list(None, text="Default text")
    [ContentBlock(text="Default text")]
    """
    if content is None:
        return [ContentBlock(**content_block_kwargs)]

    if not isinstance(content, list):
        content = [content]
    
    return [ContentBlock.model_validate(ContentBlock.coerce(c)) for c in content]



class Message(BaseModel):
    role: str
    content: List[ContentBlock]
    

    def __init__(self, role, content: Union[str, List[ContentBlock], List[Union[ContentBlock, str, ToolCall, ToolResult, ImageContent, np.ndarray, PILImage.Image, BaseModel]]] = None, **content_block_kwargs):
        content = to_content_blocks(content, **content_block_kwargs)
        
        super().__init__(content=content, role=role)

    # XXX: This choice of naming is unfortunate, but it is what it is.
    @property
    def text(self) -> str:
        """Returns all text content, replacing non-text content with their representations.

        Example:
            >>> message = Message(role="user", content=["Hello", PILImage.new('RGB', (100, 100)), "World"])
            >>> message.text
            'Hello\\n<PilImage>\\nWorld'
        """
        return _content_to_text(self.content)
    
    @property
    def images(self) -> List[ImageContent]:
        """Returns a list of all image content.

        Example:
            >>> from PIL import Image as PILImage
            >>> image1 = Image(url="https://example.com/image.jpg")
            >>> image2 = Image(image=PILImage.new('RGB', (200, 200)))
            >>> message = Message(role="user", content=["Text", image1, "More text", image2])
            >>> len(message.images)
            2
            >>> isinstance(message.images[0], Image)
            True
            >>> message.images[0].url
            'https://example.com/image.jpg'
            >>> isinstance(message.images[1].image, PILImage.Image)
            True
        """
        return [c.image for c in self.content if c.image]
    
    @property
    def audios(self) -> List[Union[np.ndarray, List[float]]]:
        """Returns a list of all audio content.

        Example:
            >>> audio1 = np.array([0.1, 0.2, 0.3])
            >>> audio2 = np.array([0.4, 0.5, 0.6])
            >>> message = Message(role="user", content=["Text", audio1, "More text", audio2])
            >>> len(message.audios)
            2
        """
        return [c.audio for c in self.content if c.audio]

    @property
    def text_only(self) -> str:
        """Returns only the text content, ignoring non-text content.

        Example:
            >>> message = Message(role="user", content=["Hello", PILImage.new('RGB', (100, 100)), "World"])
            >>> message.text_only
            'Hello\\nWorld'
        """
        return _content_to_text_only(self.content)

    @cached_property
    def tool_calls(self) -> List[ToolCall]:
        """Returns a list of all tool calls.

        Example:
            >>> tool_call = ToolCall(tool=lambda x: x, params=BaseModel())
            >>> message = Message(role="user", content=["Text", tool_call])
            >>> len(message.tool_calls)
            1
        """
        return [c.tool_call for c in self.content if c.tool_call is not None]
    
    @property
    def tool_results(self) -> List[ToolResult]:
        """Returns a list of all tool results.

        Example:
            >>> tool_result = ToolResult(tool_call_id="123", result=[ContentBlock(text="Result")])
            >>> message = Message(role="user", content=["Text", tool_result])
            >>> len(message.tool_results)
            1
        """
        return [c.tool_result for c in self.content if c.tool_result is not None]

    @property
    def parsed(self) -> Union[BaseModel, List[BaseModel]]:
        """Returns a list of all parsed content.

        Example:
            >>> class CustomModel(BaseModel):
            ...     value: int
            >>> parsed_content = CustomModel(value=42)
            >>> message = Message(role="user", content=["Text", ContentBlock(parsed=parsed_content)])
            >>> len(message.parsed)
            1
        """
        parsed_content = [c.parsed for c in self.content if c.parsed is not None]
        return parsed_content[0] if len(parsed_content) == 1 else parsed_content
    
    def call_tools_and_collect_as_message(self, parallel=False, max_workers=None):
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(c.tool_call.call_and_collect_as_content_block) for c in self.content if c.tool_call]
                content = [future.result() for future in as_completed(futures)]
        else:
            content = [c.tool_call.call_and_collect_as_content_block() for c in self.content if c.tool_call]
        return Message(role="user", content=content)

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

#XXX: Make a mixi for these properties.
def _content_to_text_only(content: List[ContentBlock]) -> str:
    return _lstr("\n").join(
            available_text
            for c in content
            if (available_text := (c.tool_result.text_only if c.tool_result else c.text))
        )

# Do we include the .text of a tool result? or its repr as in the current implementaiton?
# What is the user using .text for? I just want to see the result of the tools. text_only should get us the text of the tool results; the tool_call_id is irrelevant.
def _content_to_text(content: List[ContentBlock]) -> str:
    return _lstr("\n").join(
            available_text
            for c in content
            if (available_text :=  c.text or repr(c.content))
        )


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


