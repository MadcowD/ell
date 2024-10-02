import numpy as np
import json
from .utils import RealtimeUtils
import copy

class RealtimeConversation:
    def __init__(self):
        self.default_frequency = 24000  # 24,000 Hz
        self.clear()

    def clear(self):
        self.item_lookup = {}
        self.items = []
        self.response_lookup = {}
        self.responses = []
        self.queued_speech_items = {}
        self.queued_transcript_items = {}
        self.queued_input_audio = None
        return True

    def queue_input_audio(self, input_audio):
        self.queued_input_audio = input_audio
        return input_audio

    def process_event(self, event, *args):
        if 'event_id' not in event:
            raise ValueError("Missing 'event_id' on event")
        if 'type' not in event:
            raise ValueError("Missing 'type' on event")
        
        event_processor = getattr(self, f"_process_{event['type'].replace('.', '_')}", None)
        if not event_processor:
            raise ValueError(f"Missing conversation event processor for '{event['type']}'")
        
        return event_processor(event, *args)

    def get_item(self, id):
        return self.item_lookup.get(id)

    def get_items(self):
        return self.items.copy()

    def _process_conversation_item_created(self, event):
        item = event['item']
        new_item = copy.deepcopy(item)
        if new_item['id'] not in self.item_lookup:
            self.item_lookup[new_item['id']] = new_item
            self.items.append(new_item)
        
        new_item['formatted'] = {
            'audio': np.array([], dtype=np.int16),
            'text': '',
            'transcript': ''
        }
        
        if new_item['type'] == 'message':
            if new_item['role'] == 'user':
                new_item['status'] = 'completed'
                if self.queued_input_audio is not None:
                    new_item['formatted']['audio'] = self.queued_input_audio
                    self.queued_input_audio = None
            else:
                new_item['status'] = 'in_progress'
        elif new_item['type'] == 'function_call':
            new_item['formatted']['tool'] = {
                'type': 'function',
                'name': new_item['name'],
                'call_id': new_item['call_id'],
                'arguments': ''
            }
            new_item['status'] = 'in_progress'
        elif new_item['type'] == 'function_call_output':
            new_item['status'] = 'completed'
            new_item['formatted']['output'] = new_item['output']
        
        if new_item.get('content'):
            text_content = [c for c in new_item['content'] if c['type'] in ['text', 'input_text']]
            for content in text_content:
                new_item['formatted']['text'] += content['text']
        
        if new_item['id'] in self.queued_speech_items:
            new_item['formatted']['audio'] = self.queued_speech_items[new_item['id']]['audio']
            del self.queued_speech_items[new_item['id']]
        
        if new_item['id'] in self.queued_transcript_items:
            new_item['formatted']['transcript'] = self.queued_transcript_items[new_item['id']]['transcript']
            del self.queued_transcript_items[new_item['id']]
        
        return {'item': new_item, 'delta': None}

    def _process_conversation_item_truncated(self, event):
        item_id, audio_end_ms = event['item_id'], event['audio_end_ms']
        item = self.item_lookup.get(item_id)
        if not item:
            raise ValueError(f"item.truncated: Item '{item_id}' not found")
        
        end_index = int((audio_end_ms * self.default_frequency) / 1000)
        item['formatted']['transcript'] = ''
        item['formatted']['audio'] = item['formatted']['audio'][:end_index]
        return {'item': item, 'delta': None}

    def _process_conversation_item_deleted(self, event):
        item_id = event['item_id']
        item = self.item_lookup.get(item_id)
        if not item:
            raise ValueError(f"item.deleted: Item '{item_id}' not found")
        
        del self.item_lookup[item['id']]
        self.items = [i for i in self.items if i['id'] != item['id']]
        return {'item': item, 'delta': None}

    def _process_conversation_item_input_audio_transcription_completed(self, event):
        item_id, content_index, transcript = event['item_id'], event['content_index'], event['transcript']
        item = self.item_lookup.get(item_id)
        formatted_transcript = transcript or ' '
        
        if not item:
            self.queued_transcript_items[item_id] = {'transcript': formatted_transcript}
            return {'item': None, 'delta': None}
        
        item['content'][content_index]['transcript'] = transcript
        item['formatted']['transcript'] = formatted_transcript
        return {'item': item, 'delta': {'transcript': transcript}}

    def _process_input_audio_buffer_speech_started(self, event):
        item_id, audio_start_ms = event['item_id'], event['audio_start_ms']
        self.queued_speech_items[item_id] = {'audio_start_ms': audio_start_ms}
        return {'item': None, 'delta': None}

    def _process_input_audio_buffer_speech_stopped(self, event, input_audio_buffer):
        item_id, audio_end_ms = event['item_id'], event['audio_end_ms']
        speech = self.queued_speech_items[item_id]
        speech['audio_end_ms'] = audio_end_ms
        if input_audio_buffer is not None:
            start_index = int((speech['audio_start_ms'] * self.default_frequency) / 1000)
            end_index = int((speech['audio_end_ms'] * self.default_frequency) / 1000)
            speech['audio'] = input_audio_buffer[start_index:end_index]
        return {'item': None, 'delta': None}

    def _process_response_created(self, event):
        response = event['response']
        if response['id'] not in self.response_lookup:
            self.response_lookup[response['id']] = response
            self.responses.append(response)
        return {'item': None, 'delta': None}

    def _process_response_output_item_added(self, event):
        response_id, item = event['response_id'], event['item']
        response = self.response_lookup.get(response_id)
        if not response:
            raise ValueError(f"response.output_item.added: Response '{response_id}' not found")
        response['output'].append(item['id'])
        return {'item': None, 'delta': None}

    def _process_response_output_item_done(self, event):
        item = event['item']
        if not item:
            raise ValueError("response.output_item.done: Missing 'item'")
        found_item = self.item_lookup.get(item['id'])
        if not found_item:
            raise ValueError(f"response.output_item.done: Item '{item['id']}' not found")
        found_item['status'] = item['status']
        return {'item': found_item, 'delta': None}

    def _process_response_content_part_added(self, event):
        item_id, part = event['item_id'], event['part']
        item = self.item_lookup.get(item_id)
        if not item:
            raise ValueError(f"response.content_part.added: Item '{item_id}' not found")
        item['content'].append(part)
        return {'item': item, 'delta': None}

    def _process_response_audio_transcript_delta(self, event):
        item_id, content_index, delta = event['item_id'], event['content_index'], event['delta']
        item = self.item_lookup.get(item_id)
        if not item:
            raise ValueError(f"response.audio_transcript.delta: Item '{item_id}' not found")
        item['content'][content_index]['transcript'] += delta
        item['formatted']['transcript'] += delta
        return {'item': item, 'delta': {'transcript': delta}}

    def _process_response_audio_delta(self, event):
        item_id, content_index, delta = event['item_id'], event['content_index'], event['delta']
        item = self.item_lookup.get(item_id)
        if not item:
            raise ValueError(f"response.audio.delta: Item '{item_id}' not found")
        array_buffer = RealtimeUtils.base64_to_array_buffer(delta)
        append_values = np.frombuffer(array_buffer, dtype=np.int16)
        item['formatted']['audio'] = np.concatenate([item['formatted']['audio'], append_values])
        return {'item': item, 'delta': {'audio': append_values}}

    def _process_response_text_delta(self, event):
        item_id, content_index, delta = event['item_id'], event['content_index'], event['delta']
        item = self.item_lookup.get(item_id)
        if not item:
            raise ValueError(f"response.text.delta: Item '{item_id}' not found")
        item['content'][content_index]['text'] += delta
        item['formatted']['text'] += delta
        return {'item': item, 'delta': {'text': delta}}

    def _process_response_function_call_arguments_delta(self, event):
        item_id, delta = event['item_id'], event['delta']
        item = self.item_lookup.get(item_id)
        if not item:
            raise ValueError(f"response.function_call_arguments.delta: Item '{item_id}' not found")
        item['arguments'] += delta
        item['formatted']['tool']['arguments'] += delta
        return {'item': item, 'delta': {'arguments': delta}}