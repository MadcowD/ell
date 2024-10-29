"""
Groq provider.
"""

from ell.providers.openai import OpenAIProvider
from ell.configurator import register_provider


try:
    import groq
    class GroqProvider(OpenAIProvider):
        dangerous_disable_validation = True
        def translate_to_provider(self, *args, **kwargs):
            params = super().translate_to_provider(*args, **kwargs)
            params.pop('stream_options', None)
            assert 'response_format' not in params, 'Groq does not support response_format.'
            params['messages'] = messages_to_groq_message_format(params['messages'])
            return params
        
        def translate_from_provider(self, *args, **kwargs):
            res, meta = super().translate_from_provider(*args, **kwargs)
            if not meta['usage']:
                meta['usage'] = meta['x_groq']['usage']
            return res, meta
    register_provider(GroqProvider(), groq.Client)
except ImportError:
    pass

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

