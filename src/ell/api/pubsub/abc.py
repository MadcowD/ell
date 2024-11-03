from abc import ABC, abstractmethod
import logging
from typing import List

from fastapi import WebSocket

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
