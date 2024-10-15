"""
Groq provider.
"""

import json
import contextvars

from pydantic import BaseModel
from ell.providers.openai import OpenAIProvider
from ell.configurator import register_provider
from ell.types.message import ContentBlock, Message


# Create a context variable to hold the response_format model between to_provider and from_provider
store_response_format = contextvars.ContextVar('response_format', default=None)

try:
    import groq
    class GroqProvider(OpenAIProvider):
        dangerous_disable_validation = True
        def translate_to_provider(self, *args, **kwargs):
            params = super().translate_to_provider(*args, **kwargs)
            params.pop('stream_options', None)
            params['messages'] = messages_to_groq_message_format(params['messages'])

            # assert 'response_format' not in params, 'Groq does not support response_format.'
            # Store the response_format model between to_provider and from_provider
            response_format = params.get('response_format')
            store_response_format.set(response_format)
            if isinstance(response_format, type) and issubclass(response_format, BaseModel):
                # Groq beta JSON response does not support streaming or stop tokens
                params.pop('stream', None)
                params.pop('stop', None)
                params['response_format'] = {'type': 'json_object'}
                # Groq suggests explain how to respond with JSON in system prompt
                params['messages'] = add_json_schema_to_system_prompt(response_format, params['messages'])

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

def add_json_schema_to_system_prompt(response_format: BaseModel, messages):
    json_prompt = f'\n\nYou must respond with a JSON object compliant with following JSON schema:\n{json.dumps(response_format.model_json_schema(), indent=4)}'
    
    system_prompt = next(filter(lambda m: m['role'] == 'system', messages), None)

    if system_prompt is None:
        messages = [{'role': 'system', 'content': json_prompt}] + messages
    else:
        system_prompt['content'] += json_prompt

    return messages


def messages_to_groq_message_format(messages):
    """Assistant messages to Groq must take the format: {'role': 'assistant', 'content': <string>}"""
    # XXX: Issue #289: groq.BadRequestError: Error code: 400 - {'error': {'message': "'messages.1' : for 'role:assistant' the following must be satisfied[('messages.1.content' : value must be a string)]", 'type': 'invalid_request_error'}}
    new_messages = []
    for message in messages:
        if message['role'] == 'assistant':
            # Assistant messages must be strings
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

