import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import aiomqtt
import logging
import json


from sqlmodel import Session
from ell.stores.sql import PostgresStore, SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ell.studio.datamodels import SerializedLMPWithUses,InvocationsAggregate
from ell.studio.pubsub import MqttPubSub, NoOpPubSub, WebSocketPubSub
from ell.studio.config import Config

from ell.types import SerializedLMP
from datetime import datetime, timedelta
from sqlmodel import select

logger = logging.getLogger(__name__)


def get_serializer(config: Config):
    if config.pg_connection_string:
        return PostgresStore(config.pg_connection_string)
    elif config.storage_dir:
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
                    async with aiomqtt.Client(config.mqtt_connection_string) as mqtt:
                        logger.info("Connected to MQTT")
                        pubsub = MqttPubSub(mqtt)
                        loop = asyncio.get_event_loop()
                        task = pubsub.listen(loop)

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
    async def websocket_endpoint(websocket: WebSocket, pubsub: MqttPubSub = Depends(get_pubsub)):
        await websocket.accept()
        await pubsub.subscribe_async("all", websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming WebSocket messages if needed
        except WebSocketDisconnect:
            pubsub.unsubscribe_from_all(websocket)
            # manager.disconnect(websocket)

    
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



    @app.get("/api/invocation/{invocation_id}")
    def get_invocation(
        invocation_id: str,
        session: Session = Depends(get_session)
    ):
        invocation = serializer.get_invocations(session, lmp_filters=dict(), filters={"id": invocation_id})[0]
        return invocation

    @app.get("/api/invocations")
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

    @app.get("/api/traces/{invocation_id}")
    def get_all_traces_leading_to(
        invocation_id: str,
        session: Session = Depends(get_session)
    ):
        traces = serializer.get_all_traces_leading_to(session, invocation_id)
        return traces

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