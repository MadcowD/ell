import asyncio
import numpy as np
from .event_handler import RealtimeEventHandler
from .api import RealtimeAPI
from .conversation import RealtimeConversation
from .utils import RealtimeUtils
import json

class RealtimeClient(RealtimeEventHandler):
    def __init__(self, url=None, api_key=None, instructions='', dangerously_allow_api_key_in_browser=False, debug=False):
        super().__init__()
        self.default_session_config = {
            'modalities': ['text', 'audio'],
            'instructions': instructions,
            'voice': 'alloy',
            'input_audio_format': 'pcm16',
            'output_audio_format': 'pcm16',
            'input_audio_transcription': None,
            'turn_detection': None,
            'tools': [],
            'tool_choice': 'auto',
            'temperature': 0.8,
            'max_response_output_tokens': 4096,
        }
        self.session_config = {}
        self.transcription_models = [{'model': 'whisper-1'}]
        self.default_server_vad_config = {
            'type': 'server_vad',
            'threshold': 0.5,
            'prefix_padding_ms': 300,
            'silence_duration_ms': 200,
        }
        self.realtime = RealtimeAPI(url, api_key, dangerously_allow_api_key_in_browser, debug)
        self.conversation = RealtimeConversation()
        self._reset_config()
        self._add_api_event_handlers()

    def _reset_config(self):
        self.session_created = False
        self.tools = {}
        self.session_config = self.default_session_config.copy()
        self.input_audio_buffer = np.array([], dtype=np.int16)
        return True

    def _add_api_event_handlers(self):
        self.realtime.on('client.*', lambda event: self.dispatch('realtime.event', {
            'time': RealtimeUtils.generate_id('time_'),
            'source': 'client',
            'event': event
        }))
        self.realtime.on('server.*', lambda event: self.dispatch('realtime.event', {
            'time': RealtimeUtils.generate_id('time_'),
            'source': 'server',
            'event': event
        }))
        self.realtime.on('server.session.created', lambda _: setattr(self, 'session_created', True))
        
        def handle_conversation_event(event, *args):
            result = self.conversation.process_event(event, *args)
            if result['item']:
                self.dispatch('conversation.updated', result)
            return result

        self.realtime.on('server.response.created', handle_conversation_event)
        self.realtime.on('server.response.output_item.added', handle_conversation_event)
        self.realtime.on('server.response.content_part.added', handle_conversation_event)
        self.realtime.on('server.input_audio_buffer.speech_started', lambda event: (
            handle_conversation_event(event),
            self.dispatch('conversation.interrupted', event)
        ))
        self.realtime.on('server.input_audio_buffer.speech_stopped', lambda event: 
            handle_conversation_event(event, self.input_audio_buffer)
        )
        self.realtime.on('server.conversation.item.created', lambda event: (
            handle_conversation_event(event),
            self.dispatch('conversation.item.appended', {'item': event['item']})
        ))
        self.realtime.on('server.conversation.item.truncated', handle_conversation_event)
        self.realtime.on('server.conversation.item.deleted', handle_conversation_event)
        self.realtime.on('server.conversation.item.input_audio_transcription.completed', handle_conversation_event)
        self.realtime.on('server.response.audio_transcript.delta', handle_conversation_event)
        self.realtime.on('server.response.audio.delta', handle_conversation_event)
        self.realtime.on('server.response.text.delta', handle_conversation_event)
        self.realtime.on('server.response.function_call_arguments.delta', handle_conversation_event)
        def handle_output_item_done( event):
            handle_conversation_event(event)
            item = event.get('item', {})
            
            if item.get('status') == 'completed':
                self.dispatch('conversation.item.completed', {'item': item})
            
            formatted = item.get('formatted', {})
            tool = formatted.get('tool') if isinstance(formatted, dict) else None
            
            if tool:
                asyncio.create_task(self._call_tool(tool))
        self.realtime.on('server.response.output_item.done', handle_output_item_done)

  

    def is_connected(self):
        return self.realtime.is_connected() and self.session_created

    def reset(self):
        self.disconnect()
        self.clear_event_handlers()
        self.realtime.clear_event_handlers()
        self._reset_config()
        self._add_api_event_handlers()
        return True

    async def connect(self):
        if self.is_connected():
            raise Exception("Already connected, use .disconnect() first")
        await self.realtime.connect()
        self.update_session()
        return True

    async def wait_for_session_created(self):
        if not self.realtime.is_connected():
            raise Exception("Not connected, use .connect() first")
        while not self.session_created:
            await asyncio.sleep(0.001)
        return True

    def disconnect(self):
        self.session_created = False
        self.conversation.clear()
        if self.realtime.is_connected():
            self.realtime.disconnect()

    def get_turn_detection_type(self):
        turn_detection = self.session_config.get('turn_detection')
        if isinstance(turn_detection, dict):
            return turn_detection.get('type')
        return None

    def add_tool(self, definition, handler):
        if not definition.get('name'):
            raise ValueError("Missing tool name in definition")
        name = definition['name']
        if name in self.tools:
            raise ValueError(f"Tool '{name}' already added. Please use .remove_tool('{name}') before trying to add again.")
        if not callable(handler):
            raise ValueError(f"Tool '{name}' handler must be a function")
        self.tools[name] = {'definition': definition, 'handler': handler}
        self.update_session()
        return self.tools[name]

    def remove_tool(self, name):
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' does not exist, cannot be removed.")
        del self.tools[name]
        return True

    def delete_item(self, id):
        self.realtime.send('conversation.item.delete', {'item_id': id})
        return True

    def update_session(self, **kwargs):
        self.session_config.update(kwargs)
        use_tools = [
            {**tool.get('definition', {}), 'type': 'function'}
            for tool in self.tools.values()
        ]
        session = {**self.session_config, 'tools': use_tools}
        if self.realtime.is_connected():
            self.realtime.send('session.update', {'session': session})
        return True

    def send_user_message_content(self, content=None):
        content = content or []
        for c in content:
            if c['type'] == 'input_audio':
                if isinstance(c['audio'], (np.ndarray, bytes)):
                    c['audio'] = RealtimeUtils.array_buffer_to_base64(c['audio'])
        if content:
            self.realtime.send('conversation.item.create', {
                'item': {
                    'type': 'message',
                    'role': 'user',
                    'content': content
                }
            })
        self.create_response()
        return True

    def append_input_audio(self, array_buffer):
        if len(array_buffer) > 0:
            self.realtime.send('input_audio_buffer.append', {
                'audio': RealtimeUtils.array_buffer_to_base64(array_buffer)
            })
            self.input_audio_buffer = RealtimeUtils.merge_int16_arrays(
                self.input_audio_buffer,
                array_buffer
            )
        return True

    def create_response(self):
        if self.get_turn_detection_type() is None and len(self.input_audio_buffer) > 0:
            self.realtime.send('input_audio_buffer.commit')
            self.conversation.queue_input_audio(self.input_audio_buffer)
            self.input_audio_buffer = np.array([], dtype=np.int16)
        self.realtime.send('response.create')
        return True

    def cancel_response(self, id=None, sample_count=0):
        if not id:
            self.realtime.send('response.cancel')
            return {'item': None}
        item = self.conversation.get_item(id)
        if not item:
            raise ValueError(f"Could not find item '{id}'")
        if item['type'] != 'message' or item['role'] != 'assistant':
            raise ValueError("Can only cancel response messages with type 'message' and role 'assistant'")
        self.realtime.send('response.cancel')
        audio_index = next((i for i, c in enumerate(item['content']) if c['type'] == 'audio'), -1)
        if audio_index == -1:
            raise ValueError("Could not find audio on item to cancel")
        self.realtime.send('conversation.item.truncate', {
            'item_id': id,
            'content_index': audio_index,
            'audio_end_ms': int((sample_count / self.conversation.default_frequency) * 1000)
        })
        return {'item': item}

    async def wait_for_next_item(self):
        event = await self.wait_for_next('conversation.item.appended')
        return {'item': event['item']}

    async def wait_for_next_completed_item(self):
        event = await self.wait_for_next('conversation.item.completed')
        return {'item': event['item']}

    async def _call_tool(self, tool):
        try:
            json_arguments = json.loads(tool['arguments'])
            tool_config = self.tools.get(tool['name'])
            if not tool_config:
                raise ValueError(f"Tool '{tool['name']}' has not been added")
            result = await tool_config['handler'](json_arguments)
            self.realtime.send('conversation.item.create', {
                'item': {
                    'type': 'function_call_output',
                    'call_id': tool['call_id'],
                    'output': json.dumps(result)
                }
            })
        except Exception as e:
            self.realtime.send('conversation.item.create', {
                'item': {
                    'type': 'function_call_output',
                    'call_id': tool['call_id'],
                    'output': json.dumps({'error': str(e)})
                }
            })
        self.create_response()