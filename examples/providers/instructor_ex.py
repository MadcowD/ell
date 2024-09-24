"""
The following example shows how to implement your own provider to use ell with instructor.
These type of changes won't be added to ell but you can use this as a starting point to
implement your own provider!
"""

from typing import Any, Callable, Dict, Optional, Tuple, cast
import instructor
from openai import OpenAI
from pydantic import BaseModel

from ell.provider import EllCallParams, Metadata, Provider
from ell.providers.openai import OpenAIProvider
from ell.types.message import ContentBlock, Message

import ell

# Patch the OpenAI client with Instructor
client = instructor.from_openai(OpenAI())

class InstructorProvider(OpenAIProvider):
    def translate_to_provider(self, *args, **kwargs):
        """ This translates ell call param,eters to the provider call parameters.  IN this case instructor is jsut an openai client. 
        so we can use the openai provider to do the translation. We just need to modify a few parameters because instructor doesn't support streaming."""
        api_params= super().translate_to_provider(*args, **kwargs)
        # Streaming is not allowed by instructor.
        api_params.pop("stream", None)
        api_params.pop("stream_options", None)
        return api_params
    
    def translate_from_provider(self,provider_response,
            ell_call : EllCallParams,
            provider_call_params : Dict[str, Any],
            origin_id : str, 
            logger : Optional[Callable] = None) -> Tuple[Message, Metadata]:
        """This translates the provider response (the result of calling client.chat.completions.create with the parameters from translate_to_provider)
          to an an ell message. In this case instructor just returns a pydantic type which we can use to create an ell response model. """
        instructor_response = cast(BaseModel, provider_response) # This just means that the type is a pydantic BaseModel. 
        if logger: logger(instructor_response.model_dump_json()) # Don't forget to log for verbose mode!
        return Message(role="assistant", content=ContentBlock(parsed=instructor_response)), {}

# We then register the provider with ell. We will use InstructorProvider any time an instructor.Instructor type client is used.
ell.register_provider(InstructorProvider(), instructor.Instructor)

class UserDetail(BaseModel):
    name: str
    age: int


@ell.complex(model="gpt-4-turbo-preview", client=client, response_model=UserDetail)
def extract_user(details : str):
    return f"Extract {details}"

print(extract_user("Jason is 25 years old"))
ell.init(verbose=True)


