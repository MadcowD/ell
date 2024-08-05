from datetime import datetime
from typing import Optional, Dict, Any, List
from ell.stores.sql import SQLiteStore
from ell import __version__
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

logger = logging.getLogger(__name__)


def create_app(storage_dir: Optional[str] = None):
    storage_path = storage_dir or os.environ.get("ELL_STORAGE_DIR") or os.getcwd()
    assert storage_path, "ELL_STORAGE_DIR must be set"
    serializer = SQLiteStore(storage_path)

    app = FastAPI(title="ELL Studio", version=__version__)

    # Enable CORS for all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/lmps")
    def get_lmps(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        lmps = serializer.get_lmps(skip=skip, limit=limit)
        return lmps
    
    @app.get("/api/latest/lmps")
    def get_latest_lmps(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        lmps = serializer.get_latest_lmps(
            skip=skip, limit=limit,
            )
        return lmps

    @app.get("/api/lmps/{name_or_id:path}")
    def get_lmp(
        name_or_id: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        # Remove any leading slash if present
        name_or_id = name_or_id.lstrip("/")

        # First, try to get by name
        lmps_by_name = serializer.get_lmps(name=name_or_id, skip=skip, limit=limit)
        if lmps_by_name:
            return list(lmps_by_name)
        
        # If not found by name, try to get by ID
        lmp_by_id = serializer.get_lmps(lmp_id=name_or_id)
        if lmp_by_id:
            return list(lmp_by_id)
        
        # If still not found, check if the last part of the path is a valid lmp_id
        name_parts = name_or_id.split("/")
        if len(name_parts) > 1:
            potential_lmp_id = name_parts[-1]
            potential_name = "/".join(name_parts[:-1])
            lmps = serializer.get_lmps(name=potential_name, lmp_id=potential_lmp_id, skip=skip, limit=limit)
            if lmps:
                return list(lmps)

        raise HTTPException(status_code=404, detail="LMP not found")

    @app.get("/api/invocations")
    @app.get("/api/invocations/{name:path}")
    def get_invocations(
        name: Optional[str] = None,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        lmp_filters = {}
        if name:
            name = name.lstrip("/")
            name_parts = name.split("/")

            lmp_filters["name"] = name_parts[0]
            if len(name_parts) > 1:
                potential_lmp_id = name_parts[-1]
                lmp_filters["lmp_id"] = potential_lmp_id

        invocations = serializer.get_invocations(lmp_filters=lmp_filters, skip=skip, limit=limit)
        return invocations

    @app.post("/api/invocations/search")
    def search_invocations(
        q: str = Query(...),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100)
    ):
        invocations = serializer.search_invocations(q, skip=skip, limit=limit)
        return invocations

    @app.get("/api/traces")
    def get_consumption_graph(
    ):
        traces = serializer.get_traces()
        return traces

    @app.get("/api/traces/{invocation_id}")
    def get_all_traces_leading_to(
        invocation_id: str,
    ):
        traces = serializer.get_all_traces_leading_to(invocation_id)
        return traces

    return app

