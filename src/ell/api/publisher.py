#todo. under api-server / api.server ... maybe?
from abc import ABC, abstractmethod


class Publisher(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: str) -> None:
        pass


class NoopPublisher(Publisher):
    async def publish(self, topic: str, message: str) -> None:
        pass