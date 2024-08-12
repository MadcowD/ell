from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from functools import lru_cache
import json
import logging
from typing import Any

from aiomqtt import Topic
import aiomqtt
from fastapi import WebSocket

logger = logging.getLogger(__name__)

Subscriber = WebSocket

class PubSub(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: str) -> None:
        pass

    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        pass

    async def subscribe_async(self, topic: str, subscriber: Subscriber) -> None:
        pass

    def unsubscribe(self, topic: str, subscriber: Subscriber):
        pass

    def unsubscribe_from_all(self, subscriber: Subscriber):
        pass

@lru_cache(maxsize=128)
def matchable(topic: str) -> Topic:
    return Topic(topic)

class WebSocketPubSub(PubSub):
    def __init__(self):
        self.subscribers: dict[str, list[Subscriber]] = {} 

    async def publish(self, topic: str, message: Any):
        # Notify all subscribers for the topic
        # determine if match baased on mqtt wildcard logic
        _topic = matchable(topic)
        subscribers = self.subscribers.copy() # copy to avoid mutating while iterating
        for pattern in subscribers:  
            if _topic.matches(pattern):
                for subscriber in subscribers[pattern]:
                    asyncio.create_task(subscriber.send_json({"topic": topic, "message": message}))

    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        # Add the subscriber to the list for the topic
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(subscriber)

    def unsubscribe(self, topic: str, subscriber: Subscriber):
        subscribers = self.subscribers.copy()
        if topic in subscribers:
            self.subscribers[topic].remove(subscriber)
            if not self.subscribers[topic]:
                del self.subscribers[topic]

    def unsubscribe_from_all(self, subscriber: Subscriber):
        for topic in self.subscribers.copy():
            self.unsubscribe(topic, subscriber)

class MqttWebSocketPubSub(WebSocketPubSub):
    mqtt_client: aiomqtt.Client
    def __init__(self, conn: aiomqtt.Client):
        self.mqtt_client = conn

    def listen(self, loop: asyncio.AbstractEventLoop):
        self.listener = loop.create_task(self._relay_all())
        return self.listener
    
    async def publish(self, topic: str, message: str) -> None:
        await self.mqtt_client.publish(topic, message)
    
    async def _relay_all(self) -> None:
        async for message in self.mqtt_client.messages:
            await self.publish(str(message.topic), json.loads(str(message.payload)))

    async def subscribe_async(self, topic: str, subscriber: Subscriber) -> None:
        await self.mqtt_client.subscribe(topic)
        super().subscribe(topic, subscriber)


class NoOpPubSub(PubSub):
    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        pass

    def unsubscribe(self, topic: str, subscriber: Subscriber) -> None:
        pass

    def unsubscribe_from_all(self, subscriber: Subscriber) -> None:
        pass

    async def publish(self, topic: str, message: Any) -> None:
        pass