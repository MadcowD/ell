from abc import ABC, abstractmethod
import asyncio
from contextlib import asynccontextmanager
import json
import logging
from typing import Any, Dict, List, Set

import aiomqtt
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session
from ell.api.config import Config
from ell.api.types import GetLMPResponse, WriteLMPInput, LMP
from ell.store import Store
from ell.stores.sql import PostgresStore, SQLStore, SQLiteStore
from ell.types import Invocation,  SerializedLStr


logger = logging.getLogger(__name__)


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


publisher = None


async def get_publisher():
    yield publisher

serializer: SQLStore | None = None


def init_serializer(config: Config) -> SQLStore:
    global serializer
    if serializer is not None:
        return serializer
    elif config.pg_connection_string:
        return  PostgresStore(config.pg_connection_string)
    elif config.storage_dir:
        return SQLiteStore(config.storage_dir)
    else:
        raise ValueError("No storage configuration found")


def get_serializer():
    if serializer is None:
        raise ValueError("Serializer not initialized")
    return serializer


def get_session():
    if serializer is None:
        raise ValueError("Serializer not initialized")
    with Session(serializer.engine) as session:
        yield session


def create_app(config: Config):
    app = FastAPI(
        title="ELL API",
        description="API server for ELL",
        version="0.1.0",
        # dependencies=[Depends(get_publisher),
                    #   Depends(get_serializer)]
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global serializer
        global publisher

        logger.info("Starting lifespan")

        serializer = init_serializer(config)

        if config.mqtt_connection_string is not None:
            try:
                async with aiomqtt.Client(config.mqtt_connection_string) as mqtt:
                    logger.info("Connected to MQTT")
                    publisher = MqttPub(mqtt)
                    yield  # Allow the app to run
            except aiomqtt.MqttError as e:
                logger.error(f"Failed to connect to MQTT", exc_info=e)
                publisher = None
        else:
            publisher = NoopPublisher()
            yield  # allow the app to run

    @app.get("/lmp/{lmp_id}", response_model=GetLMPResponse)
    async def get_lmp(lmp_id: str,
                      serializer: Store = Depends(get_serializer),
                      session: Session = Depends(get_session)):
        lmp = serializer.get_lmp(lmp_id, session=session)
        if lmp is None:
            raise HTTPException(status_code=404, detail="LMP not found")

        return LMP.from_serialized_lmp(lmp)

    @app.post("/lmp")
    async def write_lmp(
        lmp: WriteLMPInput,
        uses: Dict[str, Any],  # SerializedLMPUses,
        publisher: Publisher = Depends(get_publisher),
        serializer: Store = Depends(get_serializer)
    ):
        serializer.write_lmp(lmp.to_serialized_lmp(), uses)

        loop = asyncio.get_event_loop()
        loop.create_task(
            publisher.publish(
                f"lmp/{lmp.lmp_id}/created",
                json.dumps({
                    "lmp": lmp.model_dump(),
                    "uses": uses
                }, default=str)
            )
        )

    @app.post("/invocation")
    async def write_invocation(
        invocation: Invocation,
        results: List[SerializedLStr],
        consumes: Set[str],
        publisher: Publisher = Depends(get_publisher),
        serializer: Store = Depends(get_serializer)
    ):
        serializer.write_invocation(
            invocation,
            results,
            consumes
        )
        loop = asyncio.get_event_loop()
        loop.create_task(
            publisher.publish(
                f"lmp/{invocation.lmp_id}/invoked",
                json.dumps({
                    "invocation": invocation,
                    "results": results,
                    "consumes": consumes
                })
            )
        )

    return app
