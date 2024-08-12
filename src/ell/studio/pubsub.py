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

# ################################## from https://github.com/empicano/aiomqtt/blob/bd91349f9c75482824022bcf1a8c0b1bd50f1349/aiomqtt/client.py#L1
# # SPDX-License-Identifier: BSD-3-Clause
# import dataclasses
# import sys
# from typing import Any

# from fastapi import WebSocket

# if sys.version_info >= (3, 10):
#     from typing import TypeAlias
# else:
#     from typing_extensions import TypeAlias


# MAX_TOPIC_LENGTH = 65535


# @dataclasses.dataclass(frozen=True)
# class Wildcard:
#     """MQTT wildcard that can be subscribed to, but not published to.

#     A wildcard is similar to a topic, but can optionally contain ``+`` and ``#``
#     placeholders. You can access the ``value`` attribute directly to perform ``str``
#     operations on a wildcard.

#     Args:
#         value: The wildcard string.

#     Attributes:
#         value: The wildcard string.
#     """

#     value: str

#     def __str__(self) -> str:
#         return self.value

#     def __post_init__(self) -> None:
#         """Validate the wildcard."""
#         if not isinstance(self.value, str):
#             msg = "Wildcard must be of type str"
#             raise TypeError(msg)
#         if (
#             len(self.value) == 0
#             or len(self.value) > MAX_TOPIC_LENGTH
#             or "#/" in self.value
#             or any(
#                 "+" in level or "#" in level
#                 for level in self.value.split("/")
#                 if len(level) > 1
#             )
#         ):
#             msg = f"Invalid wildcard: {self.value}"
#             raise ValueError(msg)


# WildcardLike: TypeAlias = "str | Wildcard"


# @dataclasses.dataclass(frozen=True)
# class Topic(Wildcard):
#     """MQTT topic that can be published and subscribed to.

#     Args:
#         value: The topic string.

#     Attributes:
#         value: The topic string.
#     """

#     def __post_init__(self) -> None:
#         """Validate the topic."""
#         if not isinstance(self.value, str):
#             msg = "Topic must be of type str"
#             raise TypeError(msg)
#         if (
#             len(self.value) == 0
#             or len(self.value) > MAX_TOPIC_LENGTH
#             or "+" in self.value
#             or "#" in self.value
#         ):
#             msg = f"Invalid topic: {self.value}"
#             raise ValueError(msg)

#     def matches(self, wildcard: WildcardLike) -> bool:
#         """Check if the topic matches a given wildcard.

#         Args:
#             wildcard: The wildcard to match against.

#         Returns:
#             True if the topic matches the wildcard, False otherwise.
#         """
#         if not isinstance(wildcard, Wildcard):
#             wildcard = Wildcard(wildcard)
#         # Split topics into levels to compare them one by one
#         topic_levels = self.value.split("/")
#         wildcard_levels = str(wildcard).split("/")
#         if wildcard_levels[0] == "$share":
#             # Shared subscriptions use the topic structure: $share/<group_id>/<topic>
#             wildcard_levels = wildcard_levels[2:]

#         def recurse(tl: list[str], wl: list[str]) -> bool:
#             """Recursively match topic levels with wildcard levels."""
#             if not tl:
#                 if not wl or wl[0] == "#":
#                     return True
#                 return False
#             if not wl:
#                 return False
#             if wl[0] == "#":
#                 return True
#             if tl[0] == wl[0] or wl[0] == "+":
#                 return recurse(tl[1:], wl[1:])
#             return False

#         return recurse(topic_levels, wildcard_levels)


# TopicLike: TypeAlias = "str | Topic"
# ##################################

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

class MqttPubSub(WebSocketPubSub):
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