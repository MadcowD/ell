import asyncio
from typing import Callable, Dict, List, Any

class RealtimeEventHandler:
    def __init__(self):
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.next_event_handlers: Dict[str, List[Callable]] = {}

    def clear_event_handlers(self):
        self.event_handlers.clear()
        self.next_event_handlers.clear()
        return True

    def on(self, event_name: str, callback: Callable = None):
        def decorator(func):
            if event_name not in self.event_handlers:
                self.event_handlers[event_name] = []
            self.event_handlers[event_name].append(func)
            return func

        if callback is None:
            return decorator
        else:
            return decorator(callback)

    def on_next(self, event_name: str, callback: Callable):
        if event_name not in self.next_event_handlers:
            self.next_event_handlers[event_name] = []
        self.next_event_handlers[event_name].append(callback)

    def off(self, event_name: str, callback: Callable = None):
        if event_name in self.event_handlers:
            if callback:
                self.event_handlers[event_name].remove(callback)
            else:
                del self.event_handlers[event_name]
        return True

    def off_next(self, event_name: str, callback: Callable = None):
        if event_name in self.next_event_handlers:
            if callback:
                self.next_event_handlers[event_name].remove(callback)
            else:
                del self.next_event_handlers[event_name]
        return True

    async def wait_for_next(self, event_name: str, timeout: float = None):
        next_event = None
        def set_next_event(event):
            nonlocal next_event
            next_event = event
        
        self.on_next(event_name, set_next_event)
        
        start_time = asyncio.get_event_loop().time()
        while not next_event:
            if timeout and asyncio.get_event_loop().time() - start_time > timeout:
                return None
            await asyncio.sleep(0.001)
        
        return next_event

    def dispatch(self, event_name: str, event: Any):
        handlers = self.event_handlers.get(event_name, []).copy()
        for handler in handlers:
            handler(event)
        
        next_handlers = self.next_event_handlers.pop(event_name, [])
        for next_handler in next_handlers:
            next_handler(event)
        
        return True