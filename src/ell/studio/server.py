import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import aiomqtt
import logging
import json


from sqlmodel import Session
from ell.stores.sql import PostgresStore, SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from ell.studio.config import Config
from ell.studio.connection_manager import ConnectionManager
from ell.studio.datamodels import InvocationPublicWithConsumes, SerializedLMPWithUses
from ell.studio.datamodels import SerializedLMPWithUses,InvocationsAggregate
from ell.studio.pubsub import MqttWebSocketPubSub, NoOpPubSub, WebSocketPubSub

from ell.types import SerializedLMP
from datetime import datetime, timedelta
from sqlmodel import select

logger = logging.getLogger(__name__)


from ell.studio.datamodels import InvocationsAggregate


def get_serializer(config: Config):
    if config.pg_connection_string:
        logger.info("Initializing Postgres serializer")
        return PostgresStore(config.pg_connection_string)
    elif config.storage_dir:
        logger.info("Initializing SQLite serializer")
        return SQLiteStore(config.storage_dir)
    else:
        raise ValueError("No storage configuration found")


pubsub = None

async def get_pubsub():
    yield pubsub



def create_app(config:Config):
    # setup_logging()
    serializer = get_serializer(config)

    def get_session():
        with Session(serializer.engine) as session:
            yield session


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global pubsub
        # when we're just using sqlite, handle publishes from db_watcher
        if config.storage_dir is not None:
            pubsub=WebSocketPubSub()
            yield
        elif config.mqtt_connection_string is None:
            pubsub = NoOpPubSub()
            yield
        else:
            retry_interval_seconds = 1
            retry_max_attempts = 5
            task = None

            for attempt in range(retry_max_attempts):
                try:
                    host, port = config.mqtt_connection_string.split("://")[1].split(":")

                    logger.info(f"Connecting to MQTT broker at {host}:{port}")

                    async with aiomqtt.Client(hostname=host, port=int(port) if port else 1883) as mqtt:
                        logger.info("Connected to MQTT")
                        pubsub = MqttWebSocketPubSub(mqtt)
                        loop = asyncio.get_event_loop()
                        task = pubsub.listen(loop)
                        # await pubsub.mqtt_client.subscribe("#")
                        # async for message in pubsub.mqtt_client.messages:
                        #     logger.info(f"Received message on topic {message.topic}: {message.payload}")
                        # logger.info("Subscribed to all topics")

                        yield  # Allow the app to run

                        # Clean up after yield
                        if task and not task.done():
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                pass
                        break  # Exit the retry loop if successful
                except aiomqtt.MqttError as e:
                    logger.error(f"Failed to connect to MQTT [Attempt {attempt + 1}/{retry_max_attempts}]: {e}")
                    if attempt < retry_max_attempts - 1:
                        await asyncio.sleep(retry_interval_seconds)
                    else:
                        logger.error("Max retry attempts reached. Unable to connect to MQTT.")
                        raise

            pubsub = None  # Reset pubsub after exiting the context


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
    async def websocket_endpoint(websocket: WebSocket, pubsub: MqttWebSocketPubSub = Depends(get_pubsub)):
        await websocket.accept()
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

    # used by db_watcher for sqlite
    async def notify_clients(entity: str, id: Optional[str] = None):
        if pubsub is None:
            logger.error("Pubsub not ready; cannot notify clients")
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