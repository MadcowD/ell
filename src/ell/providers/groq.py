"""
Groq provider.
"""

import json
import contextvars
from typing import List

from pydantic import BaseModel
import ell
from ell.provider import EllCallParams
from ell.providers.openai import OpenAIProvider
from ell.configurator import register_provider
from ell.types.message import ContentBlock, Message


# Create a context variable to hold the response_format model between to_provider and from_provider
store_response_format = contextvars.ContextVar('response_format', default=None)

try:
    import groq
    class GroqProvider(OpenAIProvider):
        dangerous_disable_validation = True
        def translate_to_provider(self, ell_call: EllCallParams):
            # assert 'response_format' not in params, 'Groq does not support response_format.'
            # Store the response_format model between to_provider and from_provider
            response_format = ell_call.api_params.get('response_format')
            store_response_format.set(response_format)
            if isinstance(response_format, type) and issubclass(response_format, BaseModel):
                # Groq suggests explain how to respond with JSON in system prompt
                ell_call.messages = add_json_schema_to_system_prompt(response_format, ell_call.messages)
                # Groq beta JSON response does not support streaming or stop tokens
                ell_call.api_params.pop('stream', None)
                ell_call.api_params.pop('stop', None)
                ell_call.api_params['response_format'] = {'type': 'json_object'}

            params = super().translate_to_provider(ell_call)
            params.pop('stream_options', None)
            params['messages'] = messages_to_groq_message_format(params['messages'])

            return params
        
        def translate_from_provider(self, *args, **kwargs):
            res, meta = super().translate_from_provider(*args, **kwargs)
            if not meta['usage']:
                meta['usage'] = meta['x_groq']['usage']

            response_format = store_response_format.get()
            if isinstance(response_format, type) and issubclass(response_format, BaseModel):
                json_text = res[0].content[0].text
                try:
                    parsed = response_format(**json.loads(json_text))
                    res = Message(role='assistant', content=ContentBlock(parsed=parsed))
                except Exception as e:
                    raise Exception(f"Could not parse Groq response: {json_text} into {response_format.__name__}") from e

            return res, meta
    register_provider(GroqProvider(), groq.Client)
except ImportError:
    pass

def add_json_schema_to_system_prompt(response_format: BaseModel, messages: List[Message]) -> List[Message]:
    json_prompt = f'\n\nYou must respond with a JSON object compliant with following JSON schema:\n{json.dumps(response_format.model_json_schema(), indent=4)}'
    
    system_prompt = next(filter(lambda m: m.role == 'system', messages), None)

    if system_prompt is None:
        messages = [ell.system(content=json_prompt)] + messages
    else:
        system_prompt.content.append(ContentBlock(text=json_prompt))

    return messages


def messages_to_groq_message_format(messages):
    """Assistant messages to Groq must take the format: {'role': 'assistant', 'content': <string>}"""
    # XXX: Issue #289: groq.BadRequestError: Error code: 400 - {'error': {'message': "'messages.1' : for 'role:assistant' the following must be satisfied[('messages.1.content' : value must be a string)]", 'type': 'invalid_request_error'}}
    new_messages = []
    for message in messages:
        # Assistant messages must be strings or tool calls
        if message['role'] == 'assistant' and 'tool_calls' not in message:
            # If content is a list, only one string element is allowed
            if isinstance(message['content'], str):
                new_messages.append({'role': 'assistant', 'content': message['content']})
            elif isinstance(message['content'], list) and len(message['content']) == 1 and message['content'][0]['type'] == 'text':
                new_messages.append({'role': 'assistant', 'content': message['content'][0]['text']})
            else:
                raise ValueError('Groq assistant messages must contain exactly one string content.')
        else:
            new_messages.append(message)
    
    return new_messages

