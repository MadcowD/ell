from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Any, List

from fastapi import WebSocket

from ell.util.pubsub import topic_matches, validate_publish_topic, validate_subscription_pattern

logger = logging.getLogger(__name__)

Subscriber = WebSocket


class PubSub(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: str) -> None:
        pass

    @abstractmethod
    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        pass

    @abstractmethod
    async def subscribe_async(self, topic: str, subscriber: Subscriber) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, topic: str, subscriber: Subscriber):
        pass

    @abstractmethod
    def unsubscribe_from_all(self, subscriber: Subscriber):
        pass


    @abstractmethod
    def get_subscriptions(self, subscriber: Subscriber) -> List[str]:
        pass


class WebSocketPubSub(PubSub):
    def __init__(self):
        # Topic pattern -> subscribed websockets
        self.subscriptions: dict[str, list[Subscriber]] = {}
        # Reverse index for self.subscriptions (websocket -> their subscribed topic patterns)
        self.subscribers: dict[Subscriber, list[str]] = {}

    async def publish(self, topic: str, message: Any):
        validate_publish_topic(topic)
        # Notify all subscribers whose subscription pattern is a match for `topic`
        subscriptions = self.subscriptions.copy()  # copy to avoid mutating while iterating
        logger.info(f"Relaying message to socket {topic} subscribers")
        for pattern in subscriptions:
            if topic_matches(topic, pattern):
                for subscriber in subscriptions[pattern]:
                    asyncio.create_task(subscriber.send_json(
                        {"topic": topic, "message": message}))

    def subscribe(self, topic_pattern: str, subscriber: Subscriber) -> None:
        """Subscribes the websocket `subscriber` to receive messages matching the topic pattern `topic`"""
        validate_subscription_pattern(topic_pattern)
        logger.info(f"Subscribing ws {subscriber} to {topic_pattern}")
        # Add the subscriber to the list for the topic
        if topic_pattern not in self.subscriptions:
            self.subscriptions[topic_pattern] = []
        self.subscriptions[topic_pattern].append(subscriber)
        if subscriber not in self.subscribers:
            self.subscribers[subscriber] = []
        self.subscribers[subscriber].append(topic_pattern)

    def unsubscribe(self, topic: str, subscriber: Subscriber):
        """Unsubscribes the websocket `subscriber` from the topic pattern `topic`"""
        subscriptions = self.subscriptions.copy()
        if topic in subscriptions:
            # Try to apply the edit to the original subscriptions map
            try:
                # Remove the subscriber
                self.subscriptions[topic].remove(subscriber)
                # Prune the topic from the subscriptions map if the edit resulted in 0 subscribers for the topic
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            except Exception:
                # If anything goes wrong in updating the subscriptions map, we assume it's concurrency-related
                # and the current subscriptions map contains the edit we would have made
                pass

    def unsubscribe_from_all(self, subscriber: Subscriber):
        """Removes the websocket `subscriber` from all topics. Typically called on socket disconnect."""
        subscribers = self.subscribers.copy()
        subscriber_subscriptions = subscribers[subscriber]
        if subscriber_subscriptions:
            for topic in subscriber_subscriptions:
                self.unsubscribe(topic, subscriber)
            try:
                del self.subscribers[subscriber]
            except KeyError:
                pass

    async def subscribe_async(self, topic_pattern: str, subscriber: Subscriber) -> None:
        """Subscribes the websocket `subscriber` to receive messages matching the topic pattern `topic`"""
        validate_subscription_pattern(topic_pattern)
        logger.info(f"Subscribing ws {subscriber} to {topic_pattern}")
        self.subscribe(topic_pattern, subscriber)

    def get_subscriptions(self, subscriber: Subscriber) -> List[str]:
        """Returns the list of topic patterns that the websocket `subscriber` is subscribed to"""
        return self.subscribers.get(subscriber, [])
