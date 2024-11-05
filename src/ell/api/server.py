# todo. under ell.api.server.___main___
import asyncio
from contextlib import asynccontextmanager, AsyncExitStack
import json
import logging
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException

from ell.api.client.abc import EllClient
from ell.api.config import Config
from ell.api.pubsub.abc import PubSub
from ell.types.serialize import GetLMPResponse, LMPInvokedEvent, WriteInvocationInput, WriteLMPInput, LMP

logger = logging.getLogger(__name__)

pubsub: Optional[PubSub] = None


async def get_pubsub():
    yield pubsub

async def init_pubsub(config: Config, exit_stack: AsyncExitStack):
    """Set up the appropriate pubsub client based on configuration."""
    if config.mqtt_connection_string is not None:
        try:
            from ell.api.pubsub.mqtt import setup
        except ImportError as e:
            raise ImportError(
                "Received mqtt_connection_string but dependencies missing. Install with `pip install -U ell-ai[mqtt]. More info: https://docs.ell.so/installation") from e

        pubsub, mqtt_client = await setup(config.mqtt_connection_string)

        exit_stack.push_async_exit(mqtt_client)

        loop = asyncio.get_event_loop()
        return pubsub, pubsub.listen(loop)

    return None, None



serializer: Optional[EllClient] = None


def init_serializer(config: Config) -> EllClient:
    global serializer
    if serializer is not None:
        return serializer
    elif config.pg_connection_string:
        try:
            from ell.api.client.postgres import EllPostgresClient
            return EllPostgresClient(config.pg_connection_string)
        except ImportError:
            # todo. centralize this in util or something, we have it everywhere
            raise ImportError(
                "Postgres storage is not enabled. Enable it with `pip install -U ell-api[postgres]`. More info: https://docs.ell.so/installation")
    elif config.storage_dir:
        try:
            from ell.api.client.sqlite import EllSqliteClient
            return EllSqliteClient(config.storage_dir)
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


def create_app(config: Config):
    # setup_logging(config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global serializer
        global pubsub
        exit_stack = AsyncExitStack()
        pubsub_task = None

        logger.info("Starting lifespan")

        serializer = init_serializer(config)

        try:
            pubsub, pubsub_task = await init_pubsub(config, exit_stack)
            yield

        finally:
            if pubsub_task and not pubsub_task.done():
                pubsub_task.cancel()
                try:
                    await pubsub_task
                except asyncio.CancelledError:
                    pass

            await exit_stack.aclose()
            pubsub = None

    app = FastAPI(
        title="ELL API",
        description="Ell API Server",
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
            pubsub: PubSub = Depends(get_pubsub),
            serializer: EllClient = Depends(get_serializer)
    ):
        await serializer.write_lmp(lmp, uses)

        if pubsub:
            loop = asyncio.get_event_loop()
            loop.create_task(
                pubsub.publish(
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
            pubsub: PubSub = Depends(get_pubsub),
            serializer: EllClient = Depends(get_serializer)
    ):
        logger.info(f"Writing invocation {input.invocation.lmp_id}")
        # TODO: return anything this might create like invocation id
        result = await serializer.write_invocation(input)

        if pubsub:
            loop = asyncio.get_event_loop()
            loop.create_task(
                pubsub.publish(
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
