import asyncio
import json
import logging

import aiomqtt

from ell.api.pubsub.abc import Subscriber
from ell.api.pubsub.websocket import WebSocketPubSub

logger = logging.getLogger(__name__)


class MqttWebSocketPubSub(WebSocketPubSub):
    mqtt_client: aiomqtt.Client

    def __init__(self, conn: aiomqtt.Client):
        super().__init__()
        self.mqtt_client = conn

    def listen(self, loop: asyncio.AbstractEventLoop):
        self.listener = loop.create_task(self._relay_all())
        return self.listener

    async def publish(self, topic: str, message: str) -> None:
        # this is a bit sus because we could get in a loop if the message is echoed back
        # we're also publishing to mqtt, not websocket clients
        await self.mqtt_client.publish(topic, message)

    async def _relay_all(self) -> None:
        """
        Relays all messages received on the subscribed MQTT topics to the websocket subscribers on the same topics.

        Example:
            self.subscribe("detailed-telemetry/#")  # <- Registers us to receive MQTT messages published to detailed-telemetry/1, detailed-telemetry/2, ...

            Upon receipt, we forward these messages to any connected Ell Studio websockets whose subscription matches the published topic .

            i.e.:
            Subscriptions map:
              "detailed-telemetry/1" -> [socket1]
              "detailed-telemetry/2" -> [socket2]
              "lmp/#" -> [socket1, socket2]
            - An MQTT message published to detailed-telemetry/1 will be relayed to socket1
            - An MQTT message published to lmp/42 will be relayed to socket1 and socket2


        """
        logger.info("Starting mqtt listener")
        async for message in self.mqtt_client.messages:
            try:
                logger.debug(f"Received message on topic {message.topic}: {message.payload}")
                # Call the websocket's publish method to publish the message received from MQTT to the websocket
                await super().publish(str(message.topic), json.loads(
                    message.payload  # type: ignore
                ))
            except Exception as e:
                logger.error(f"Error relaying message: {e}")

    async def subscribe_async(self, topic: str, subscriber: Subscriber) -> None:
        await self.mqtt_client.subscribe(topic)
        super().subscribe(topic, subscriber)


async def setup(
        mqtt_connection_string: str,
        retry_interval_seconds: int = 1,
        retry_max_attempts: int = 5
) -> tuple[MqttWebSocketPubSub, aiomqtt.Client]:  # type: ignore
    """
    Connect to the MQTT broker at `mqtt_connection_string` using the provided retry policy.
    Returns the client and the open connection which should be handled by an AsyncExitStack or similar.
    """
    for attempt in range(retry_max_attempts):
        try:
            host, port = mqtt_connection_string.split("://")[1].split(":")
            logger.info(f"Connecting to MQTT broker at {host}:{port}")

            # Create the client - it will connect when used as context manager
            mqtt_client = aiomqtt.Client(hostname=host, port=int(port) if port else 1883)
            # We call __aenter__ here in order to connect and retry on failure
            # The client is passed back and must be handled with __aclose__()
            await mqtt_client.__aenter__()
            return MqttWebSocketPubSub(mqtt_client), mqtt_client

        except aiomqtt.MqttError as e:
            logger.error(f"Failed to connect to MQTT [Attempt {attempt + 1}/{retry_max_attempts}]: {e}")
            if attempt < retry_max_attempts - 1:
                await asyncio.sleep(retry_interval_seconds)
                continue
            else:
                logger.error("Max retry attempts reached. Unable to connect to MQTT.")
                raise ValueError(f"Failed to connect to MQTT after {retry_max_attempts} attempts") from e
