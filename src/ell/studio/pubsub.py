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
        self.subscriptions: dict[str, list[Subscriber]] = {}

    async def publish(self, topic: str, message: Any):
        # Notify all subscribers for the topic
        # determine if match baased on mqtt wildcard logic
        _topic = matchable(topic)
        subscriptions = self.subscriptions.copy()  # copy to avoid mutating while iterating
        logger.info(f"Relaying message to socket {topic} subscribers")
        for pattern in subscriptions:
            if _topic.matches(pattern):
                for subscriber in subscriptions[pattern]:
                    asyncio.create_task(subscriber.send_json(
                        {"topic": topic, "message": message}))

    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        logger.info(f"Subscribing ws {subscriber} to {topic}")
        # Add the subscriber to the list for the topic
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(subscriber)

    def unsubscribe(self, topic: str, subscriber: Subscriber):
        subscriptions = self.subscriptions.copy()
        if topic in subscriptions:
            self.subscriptions[topic].remove(subscriber)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]

    def unsubscribe_from_all(self, subscriber: Subscriber):
        for topic in self.subscriptions.copy():
            self.unsubscribe(topic, subscriber)


class MqttWebSocketPubSub(WebSocketPubSub):
    mqtt_client: aiomqtt.Client

    def __init__(self, conn: aiomqtt.Client):
        super().__init__()
        self.mqtt_client = conn

    def listen(self, loop: asyncio.AbstractEventLoop):
        self.listener = loop.create_task(self._relay_all())
        return self.listener

    async def publish(self, topic: str, message: str) -> None:
        # this is a bit sus
        await self.mqtt_client.publish(topic, message)

    async def _relay_all(self) -> None:
        logger.info("Starting mqtt listener")
        async for message in self.mqtt_client.messages:
            try:
                logger.info(f"Received message on topic {
                            message.topic}: {message.payload}")
                await super().publish(str(message.topic), json.loads(
                    message.payload  # type: ignore
                ))
            except Exception as e:
                logger.error(f"Error relaying message: {e}")

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
