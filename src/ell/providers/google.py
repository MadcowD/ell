from typing import Any, Callable, Dict, FrozenSet, Iterator, List, Literal, Optional, Tuple, Type, TypedDict, Union, cast
from ell.provider import  EllCallParams, Metadata, Provider
from ell.types import Message, ContentBlock, ToolCall, ImageContent

from ell.types._lstr import _lstr
from ell.types.message import LMP
from ell.configurator import register_provider
from ell.util.serialization import serialize_image
import base64
from io import BytesIO
import json
import requests
from PIL import Image as PILImage

# XXX: Not supported:
# tool use
# function calling
# structured output
try:

    from google import genai
    import google.genai.types as types

    class MessageCreateParamsStreaming(TypedDict):
        model: str
        contents: Union[types.ContentListUnion, types.ContentListUnionDict]
        config: Optional[types.GenerateContentConfigOrDict]

    
    class GoogleProvider(Provider):
        dangerous_disable_validation = False
           
        def provider_call_function(self, client : genai.Client, api_call_params : Optional[Dict[str, Any]] = None) -> Callable[..., Any]:
            return client.models.generate_content_stream
        
        def disallowed_api_params(self) -> FrozenSet[str]:
            return frozenset({"messages", "tools", "model", "stream", "stream_options", "system_instruction", "n"})
        
        def translate_to_provider(self, ell_call : EllCallParams) -> MessageCreateParamsStreaming: 
            # final_call_params = cast(MessageCreateParamsStreaming, ell_call.api_params.copy())
            # # XXX: Helper, but should be depreicated due to ssot
            assert not ell_call.tools, "Provider does not yet support tools"

            clean_api_params = ell_call.api_params.copy()
            clean_api_params.pop("stream", None)
            if "max_tokens" in clean_api_params:
                clean_api_params["max_output_tokens"] = clean_api_params.pop("max_tokens")
            
            msgs = [
                types.Content(
                    role=message.role if message.role in ['system', 'user'] else 'model',
                    parts=[
                        _content_block_to_google_format(c)
                        for c in message.content
                    ]
                )
                for message in ell_call.messages
            ]

            system_instruction : Optional[types.ContentUnion] = None
            system_msg = next((m for m in msgs if m.role == "system"), None)
            if system_msg:
                system_instruction = system_msg
                msgs = [m for m in msgs if m.role != "system"]
            
            
            return MessageCreateParamsStreaming(
                model=ell_call.model,
                contents=msgs,
                config=types.GenerateContentConfig(
                    **clean_api_params, 
                    system_instruction=system_instruction,
                    response_modalities=["text"], # Text only for now
                    automatic_function_calling=None, # TODO: Support.
                    ) # performs pydantic calidation.
            )
    
        def translate_from_provider(
            self,
            provider_response : Iterator[types.GenerateContentResponse],
            ell_call: EllCallParams,
            provider_call_params: Dict[str, Any],
            origin_id: Optional[str] = None,
            logger: Optional[Callable[..., None]] = None,
        ) -> Tuple[List[Message], Metadata]:
            
            usage = {}
            metadata = {}

            #XXX: Support n > 0

            message_metadata : Optional[types.GenerateContentResponseUsageMetadata]  = None
            total_text = ""
            for chunk in provider_response:
                message_metadata = chunk.usage_metadata if chunk.usage_metadata else message_metadata
                text = chunk.text
                if text:
                    if logger: logger(text)
                total_text += text
            content = [ContentBlock(text=_lstr(total_text,origin_trace=origin_id))]
            
           
            # process metadata for ell
            # XXX: Unify an ell metadata format for ell studio.
            if message_metadata: 
                usage["prompt_tokens"] = message_metadata.prompt_token_count
                usage["completion_tokens"] = message_metadata.candidates_token_count
                usage["total_tokens"] = message_metadata.total_token_count

                metadata["usage"] = usage
            
            return [Message(role="assistant", content=content)], metadata

    # XXX: Make a singleton.
    google_provider = GoogleProvider()
    register_provider(google_provider, genai.Client)

except ImportError:
    pass

def serialize_image_for_google(img : ImageContent):
    if img.url:
        # Download the image from the URL
        response = requests.get(img.url)
        response.raise_for_status()  # Raise an exception for bad responses
        pil_image = PILImage.open(BytesIO(response.content))
    elif img.image:
        pil_image = img.image
    else:
        raise ValueError("Image object has neither url nor image data.")
    # Convert PIL Image to bytes in memory
    img_bytes_io= BytesIO()
    pil_image.save(img_bytes_io, format='PNG')
    img_byte_arr = img_bytes_io.getvalue()
    
    return dict(
        inline_data=dict(
            mime_type="image/png",
            data=img_byte_arr
        )
    )

def _content_block_to_google_format(content_block: ContentBlock):# -> "types.PartUnion"
        if (image := content_block.image): return serialize_image_for_google(image)
        elif ((text := content_block.text) is not None): return dict(text=text)
        elif (parsed := content_block.parsed):
            return dict(text=json.dumps(parsed.model_dump(), ensure_ascii=False))
        # elif (tool_call := content_block.tool_call):
        #     return dict(
        #         type="tool_use",
        #         id=tool_call.tool_call_id,
        #         name=tool_call.tool.__name__,
        #         input=tool_call.params.model_dump()
        #     )
        # elif (tool_result := content_block.tool_result):
        #     return dict(
        #         type="tool_result",
        #         tool_use_id=tool_result.tool_call_id,
        #         content=[_content_block_to_google_format(c) for c in tool_result.result]
        #     )
        else:
            raise ValueError("Content block is not supported by anthropic")
