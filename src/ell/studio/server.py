import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from sqlmodel import Session

from ell.serialize.serializer import get_serializer, get_blob_store
from ell.serialize.config import SerializeConfig
from ell.stores.sql import PostgresStore, SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from ell.studio.config import Config
from ell.studio.datamodels import InvocationPublicWithConsumes, SerializedLMPWithUses

from ell.stores.studio import SerializedLMP
from datetime import datetime, timedelta
from sqlmodel import select
from contextlib import AsyncExitStack


from ell.api.pubsub.abc import PubSub
from ell.api.pubsub.websocket import WebSocketPubSub

logger = logging.getLogger(__name__)


from ell.studio.datamodels import InvocationsAggregate


def get_serializer(config: Config):
    serialize_config = SerializeConfig(**config.model_dump())
    blob_store = get_blob_store(serialize_config)
    if config.pg_connection_string:
        return PostgresStore(config.pg_connection_string, blob_store)
    elif config.storage_dir:
        return SQLiteStore(config.storage_dir, blob_store)
    else:
        raise ValueError("No storage configuration found")


pubsub: Optional[PubSub] = None

async def get_pubsub():
    yield pubsub


async def setup_pubsub(config: Config, exit_stack: AsyncExitStack):
    """Set up the appropriate pubsub client based on configuration."""
    if config.storage_dir is not None:
        return WebSocketPubSub(), None

    if config.mqtt_connection_string is not None:
        try:
            from ell.api.pubsub.mqtt import setup
        except ImportError as e:
            raise ImportError(
                "Received mqtt_connection_string but dependencies missing. Install with `pip install -U ell-ai[mqtt]. More info: https://docs.ell.so/installation") from e

        pubsub, mqtt_client = await setup(config.mqtt_connection_string)
        exit_stack.push_async_exit(mqtt_client)
        logger.info("Connected to MQTT")

        loop = asyncio.get_event_loop()
        return pubsub, pubsub.listen(loop)

    return None, None

def create_app(config:Config):
    serializer = get_serializer(config)

    def get_session():
        with Session(serializer.engine) as session:
            yield session

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global pubsub
        exit_stack = AsyncExitStack()
        pubsub_task = None

        try:
            pubsub, pubsub_task = await setup_pubsub(config, exit_stack)
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


    app = FastAPI(title="ell Studio", version=__version__, lifespan=lifespan)

    # Enable CORS for all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket,pubsub: PubSub = Depends(get_pubsub)):
        await websocket.accept()
        # NB. for now, studio does not dynamically subscribe to data topics. We subscribe every client to these by
        # default. If desired, apps may issue a "subscribe" message that we can handle in websocket.receive_text below
        # to sign up to receive data from arbitrary topics. They can unsubscribe when done via an "unsubscribe" message.
        await pubsub.subscribe_async("all", websocket)
        await pubsub.subscribe_async("lmp/#", websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming WebSocket messages if needed
        except WebSocketDisconnect:
            pubsub.unsubscribe_from_all(websocket)

    
    @app.get("/api/latest/lmps", response_model=list[SerializedLMPWithUses])
    def get_latest_lmps(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        lmps = serializer.get_latest_lmps(
            session,
            skip=skip, limit=limit,
            )
        return lmps

    # TOOD: Create a get endpoint to efficient get on the index with /api/lmp/<lmp_id>
    @app.get("/api/lmp/{lmp_id}")
    def get_lmp_by_id(lmp_id: str, session: Session = Depends(get_session)):
        lmp = serializer.get_lmps(session, lmp_id=lmp_id)[0]
        return lmp



    @app.get("/api/lmps", response_model=list[SerializedLMPWithUses])
    def get_lmp(
        lmp_id: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        
        filters : Dict[str, Any] = {}
        if name:
            filters['name'] = name
        if lmp_id:
            filters['lmp_id'] = lmp_id

        lmps = serializer.get_lmps(session, skip=skip, limit=limit, **filters)
        
        if not lmps:
            raise HTTPException(status_code=404, detail="LMP not found")
        
        print(lmps[0])
        return lmps



    @app.get("/api/invocation/{invocation_id}", response_model=InvocationPublicWithConsumes)
    def get_invocation(
        invocation_id: str,
        session: Session = Depends(get_session)
    ):
        invocation = serializer.get_invocations(session, lmp_filters=dict(), filters={"id": invocation_id})[0]
        return invocation

    @app.get("/api/invocations", response_model=list[InvocationPublicWithConsumes])
    def get_invocations(
        id: Optional[str] = Query(None),
        hierarchical: Optional[bool] = Query(False),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        lmp_name: Optional[str] = Query(None),
        lmp_id: Optional[str] = Query(None),
        session: Session = Depends(get_session)
    ):
        lmp_filters = {}
        if lmp_name:
            lmp_filters["name"] = lmp_name
        if lmp_id:
            lmp_filters["lmp_id"] = lmp_id

        invocation_filters = {}
        if id:
            invocation_filters["id"] = id

        invocations = serializer.get_invocations(
            session,
            lmp_filters=lmp_filters,
            filters=invocation_filters,
            skip=skip,
            limit=limit,
            hierarchical=hierarchical
        )
        return invocations


    @app.get("/api/traces")
    def get_consumption_graph(
        session: Session = Depends(get_session)
    ):
        traces = serializer.get_traces(session)
        return traces



    @app.get("/api/blob/{blob_id}", response_class=Response)
    def get_blob(
        blob_id: str,
        session: Session = Depends(get_session)
    ):
        if serializer.blob_store is None:
            raise HTTPException(status_code=400, detail="Blob storage is not configured")
        try:
            blob_data = serializer.blob_store.retrieve_blob(blob_id)
            return Response(content=blob_data.decode('utf-8'), media_type="application/json")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Blob not found")
        except Exception as e:
            logger.error(f"Error retrieving blob: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/api/lmp-history")
    def get_lmp_history(
        days: int = Query(365, ge=1, le=3650),  # Default to 1 year, max 10 years
        session: Session = Depends(get_session)
    ):
        # Calculate the start date
        start_date = datetime.utcnow() - timedelta(days=days)

        # Query to get all LMP creation times within the date range
        query = (
            select(SerializedLMP.created_at)
            .where(SerializedLMP.created_at >= start_date)
            .order_by(SerializedLMP.created_at)
        )

        results = session.exec(query).all()

        # Convert results to a list of dictionaries
        history = [{"date": str(row), "count": 1} for row in results]

        return history

    # Used by studio to publish changes from a SQLLite store directly
    async def notify_clients(entity: str, id: Optional[str] = None):
        if pubsub is None:
            logger.error("No pubsub client, cannot notify clients")
            return
        message = json.dumps({"entity": entity, "id": id})
        await pubsub.publish("all", message)

    # Add this method to the app object
    app.notify_clients = notify_clients

 
    @app.get("/api/invocations/aggregate", response_model=InvocationsAggregate)
    def get_invocations_aggregate(
        lmp_name: Optional[str] = Query(None),
        lmp_id: Optional[str] = Query(None),
        days: int = Query(30, ge=1, le=365),
        session: Session = Depends(get_session)
    ):
        lmp_filters = {}
        if lmp_name:
            lmp_filters["name"] = lmp_name
        if lmp_id:
            lmp_filters["lmp_id"] = lmp_id

        aggregate_data = serializer.get_invocations_aggregate(session, lmp_filters=lmp_filters, days=days)
        return InvocationsAggregate(**aggregate_data)
    
    
    
    return app