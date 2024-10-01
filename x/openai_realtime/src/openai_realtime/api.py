import asyncio
import json
import websockets
from .event_handler import RealtimeEventHandler
from .utils import RealtimeUtils

class RealtimeAPI(RealtimeEventHandler):
    def __init__(self, url=None, api_key=None, dangerously_allow_api_key_in_browser=False, debug=False):
        super().__init__()
        self.default_url = 'wss://api.openai.com/v1/realtime'
        self.url = url or self.default_url
        self.api_key = api_key
        self.debug = debug
        self.ws = None

    def is_connected(self):
        return self.ws is not None and self.ws.open

    def log(self, *args):
        if self.debug:
            print(*args)
        return True

    async def connect(self, model='gpt-4o-realtime-preview-2024-10-01'):
        if self.is_connected():
            raise Exception("Already connected")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'OpenAI-Beta': 'realtime=v1'
        }
        
        self.ws = await websockets.connect(f"{self.url}?model={model}", extra_headers=headers)
        
        self.log(f"Connected to {self.url}")
        
        asyncio.create_task(self._message_handler())
        
        return True

    async def _message_handler(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                self.receive(data['type'], data)
        except websockets.exceptions.ConnectionClosed:
            self.disconnect()
            self.dispatch('close', {'error': True})

    def disconnect(self):
        if self.ws:
            asyncio.create_task(self.ws.close())
            self.ws = None
        return True

    def receive(self, event_name, event):
        self.log("received:", event_name, event)
        self.dispatch(f"server.{event_name}", event)
        self.dispatch("server.*", event)
        return True

    def send(self, event_name, data=None):
        if not self.is_connected():
            raise Exception("RealtimeAPI is not connected")
        
        data = data or {}
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        
        event = {
            "event_id": RealtimeUtils.generate_id("evt_"),
            "type": event_name,
            **data
        }
        
        self.dispatch(f"client.{event_name}", event)
        self.dispatch("client.*", event)
        self.log("sent:", event_name, event)
        
        asyncio.create_task(self.ws.send(json.dumps(event)))
        return True