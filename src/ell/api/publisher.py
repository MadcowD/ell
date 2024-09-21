from abc import ABC, abstractmethod

import aiomqtt


class Publisher(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: str) -> None:
        pass


class MqttPub(Publisher):
    def __init__(self, conn: aiomqtt.Client):
        self.mqtt_client = conn

    async def publish(self, topic: str, message: str) -> None:
        await self.mqtt_client.publish(topic, message)


class NoopPublisher(Publisher):
    async def publish(self, topic: str, message: str) -> None:
        pass