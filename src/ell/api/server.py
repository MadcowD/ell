# todo. under ell.api.server.___main___
import asyncio
from contextlib import asynccontextmanager
import json
import logging
from typing import List, Optional

# fixme. get this out of here
import aiomqtt
from fastapi import Depends, FastAPI, HTTPException

from ell.api.client import EllClient, EllPostgresClient, EllSqliteClient
from ell.api.config import Config
from ell.api.publisher import NoopPublisher, Publisher
from ell.types.serialize import GetLMPResponse, LMPInvokedEvent, WriteInvocationInput, WriteLMPInput, LMP

logger = logging.getLogger(__name__)

publisher: Optional[Publisher] = None


async def get_publisher():
    yield publisher


serializer: Optional[EllClient] = None


def init_serializer(config: Config) -> EllClient:
    global serializer
    if serializer is not None:
        return serializer
    elif config.pg_connection_string:
        try:
            from ell.api.client import EllPostgresClient
            return EllPostgresClient(config.pg_connection_string)
        except ImportError:
            # todo. centralize this in util or something, we have it everywhere
            raise ImportError(
                "Postgres storage is not enabled. Enable it with `pip install -U ell-api[postgres]`. More info: https://docs.ell.so/installation")
    elif config.storage_dir:
        try:
            from ell.api.client import EllSqliteClient
            return EllSqliteClient(config.pg_connection_string)
        except ImportError:
            raise ImportError(
                "SQLite storage is not enabled. Enable it with `pip install -U ell-api[sqlite]`. More info: https://docs.ell.so/installation"
            )

    else:
        raise ValueError("No storage configuration found")


def get_serializer():
    if serializer is None:
        raise ValueError("Serializer not initialized")
    return serializer


# def get_session():
#     if serializer is None:
#         raise ValueError("Serializer not initialized")
#     with Session(serializer.engine) as session:
#         yield session


def create_app(config: Config):
    # setup_logging(config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global serializer
        global publisher

        logger.info("Starting lifespan")

        serializer = init_serializer(config)

        if config.mqtt_connection_string is not None:
            try:
                from ell.api.mqtt_publisher import MqttPub
            except ImportError:
                raise ImportError("Missing MQTT dependencies. Install them with `pip install -U ell-ai[mqtt]")

            # fixme. have the class do all of this if possible
            host, port = config.mqtt_connection_string.split("://")[1].split(":")

            logger.info(f"Connecting to MQTT broker at {host}:{port}")
            try:
                async with aiomqtt.Client(host, int(port) if port else 1883) as mqtt:
                    logger.info("Connected to MQTT")
                    publisher = MqttPub(mqtt)
                    yield  # Allow the app to run
            except aiomqtt.MqttError as e:
                logger.error(f"Failed to connect to MQTT", exc_info=e)
                publisher = None
        else:
            publisher = NoopPublisher()
            yield  # allow the app to run

    app = FastAPI(
        title="ELL API",
        description="API server for ELL",
        version="0.1.0",
        lifespan=lifespan
    )

    @app.get("/lmp/versions", response_model=List[LMP])
    async def get_lmp_versions(
            fqn: str,
            serializer: EllClient = Depends(get_serializer)):
        return serializer.get_lmp_versions(fqn)

    @app.get("/lmp/{lmp_id}", response_model=GetLMPResponse)
    async def get_lmp(lmp_id: str,
                      serializer: EllClient = Depends(get_serializer),
                      # todo. figure out the ramifications of doing this here
                      # session: Session = Depends(get_session)
                      ):
        lmp = await serializer.get_lmp(lmp_id=lmp_id)
        if lmp is None:
            raise HTTPException(status_code=404, detail="LMP not found")
        return lmp

    @app.post("/lmp")
    async def write_lmp(
            lmp: WriteLMPInput,
            # fixme. what is this type supposed to be?
            uses: List[str],  # SerializedLMPUses,
            publisher: Publisher = Depends(get_publisher),
            serializer: EllClient = Depends(get_serializer)
    ):
        await serializer.write_lmp(lmp, uses)

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

    @app.post("/invocation", response_model=WriteInvocationInput)
    async def write_invocation(
            input: WriteInvocationInput,
            publisher: Publisher = Depends(get_publisher),
            serializer: EllClient = Depends(get_serializer)
    ):
        logger.info(f"Writing invocation {input.invocation.lmp_id}")
        # TODO: return anything this might create like invocation id
        result = await serializer.write_invocation(input)

        loop = asyncio.get_event_loop()
        loop.create_task(
            publisher.publish(
                f"lmp/{input.invocation.lmp_id}/invoked",
                LMPInvokedEvent(
                    lmp_id=input.invocation.lmp_id,
                    # invocation_id=invo.id,
                    # todo. return data from write invocation
                    consumes=[]
                ).model_dump_json()
            )
        )
        return input

    return app
