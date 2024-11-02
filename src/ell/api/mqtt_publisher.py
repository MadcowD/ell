# nb this is to keep aiomqtt optional and out of everything else
import aiomqtt

from ell.api.publisher import Publisher


class MqttPub(Publisher):
    def __init__(self, conn: aiomqtt.Client):
        self.mqtt_client = conn

    async def publish(self, topic: str, message: str) -> None:
        await self.mqtt_client.publish(topic, message)

