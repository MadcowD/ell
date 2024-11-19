from typing import Optional, Dict, Any, List

from sqlmodel import Session
from ell.stores.sql import PostgresStore, SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
from ell.studio.config import Config
from ell.studio.connection_manager import ConnectionManager
from ell.studio.datamodels import EvaluationResultDatapointPublic, InvocationPublicWithConsumes, SerializedLMPWithUses, EvaluationPublic, SpecificEvaluationRunPublic

from ell.stores.models.core import SerializedLMP
from datetime import datetime, timedelta
from sqlmodel import select
from ell.stores.models.evaluations import SerializedEvaluation


logger = logging.getLogger(__name__)


from ell.studio.datamodels import InvocationsAggregate


def get_serializer(config: Config):
    if config.pg_connection_string:
        return PostgresStore(config.pg_connection_string)
    elif config.storage_dir:
        return SQLiteStore(config.storage_dir)
    else:
        raise ValueError("No storage configuration found")



def create_app(config:Config):
    serializer = get_serializer(config)

    def get_session():
        with Session(serializer.engine) as session:
            yield session

    app = FastAPI(title="ell Studio", version=__version__)

    # Enable CORS for all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    manager = ConnectionManager()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming WebSocket messages if needed
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    
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

    async def notify_clients(entity: str, id: Optional[str] = None):
        message = json.dumps({"entity": entity, "id": id})
        await manager.broadcast(message)

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
    
    
    
    @app.get("/api/evaluations", response_model=List[EvaluationPublic])
    def get_evaluations(
        evaluation_id: Optional[str] = Query(None),
        lmp_id: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        filters: Dict[str, Any] = {}
        if evaluation_id:
            filters['id'] = evaluation_id
        if lmp_id:
            filters['lmp_id'] = lmp_id

        evaluations = serializer.get_evaluations(
            session,
            filters=filters,
            skip=skip,
            limit=limit
        )


        return evaluations
    
    @app.get("/api/latest/evaluations", response_model=List[EvaluationPublic])
    def get_latest_evaluations(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        evaluations = serializer.get_latest_evaluations(
            session,
            skip=skip,
            limit=limit
        )

        return evaluations

    @app.get("/api/evaluation/{evaluation_id}", response_model=EvaluationPublic)
    def get_evaluation(
        evaluation_id: str,
        session: Session = Depends(get_session)
    ):
        evaluation = serializer.get_evaluations(session, filters={"id": evaluation_id})
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        return evaluation[0]
    
    

    @app.get("/api/evaluation-runs/{run_id}", response_model=SpecificEvaluationRunPublic)
    def get_evaluation_run(
        run_id: str,
        session: Session = Depends(get_session)
    ):
        runs = serializer.get_evaluation_run(session, run_id)
        return runs
    
    @app.get("/api/evaluation-runs/{run_id}/results", response_model=List[EvaluationResultDatapointPublic])
    def get_evaluation_run_results(
        run_id: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        results = serializer.get_evaluation_run_results(
            session,
            run_id,
            skip=skip,
            limit=limit,
        )
        return results
    
    @app.get("/api/all-evaluations", response_model=List[EvaluationPublic])
    def get_all_evaluations(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        session: Session = Depends(get_session)
    ):
        # Get all evaluations ordered by creation date, without deduplication
        query = (
            select(SerializedEvaluation)
            .order_by(SerializedEvaluation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        results = session.exec(query).all()
        return list(results)
    
    @app.get("/api/dataset/{dataset_id}")
    def get_dataset(
        dataset_id: str,
        session: Session = Depends(get_session)
    ):
        if not serializer.blob_store:
            raise HTTPException(status_code=400, detail="Blob storage not configured")
        
        try:
            # Get the blob data
            blob_data = serializer.blob_store.retrieve_blob(dataset_id)

            
            # Check if size is under 5MB
            if len(blob_data) > 5 * 1024 * 1024:  # 5MB in bytes
                raise HTTPException(
                    status_code=413,
                    detail="Dataset too large to preview (>5MB)"
                )
            
            # Decode and parse JSON
            dataset_json = json.loads(blob_data.decode('utf-8'))
            
            return {
                "size": len(blob_data),
                "data": dataset_json
            }
            
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset not found")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON data")
        except Exception as e:
            logger.error(f"Error retrieving dataset: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    return app
