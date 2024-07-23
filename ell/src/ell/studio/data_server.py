from datetime import datetime
from typing import Optional, Dict, Any, List
from ell.stores.sql import SQLiteStore
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

def create_app(storage_dir: Optional[str] = None):
    storage_path = storage_dir or os.environ.get('ELL_STORAGE_DIR') or os.getcwd()
    assert storage_path, "ELL_STORAGE_DIR must be set"
    serializer = SQLiteStore(storage_path)
    app = FastAPI()

    # Enable CORS for all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get('/api/lmps')
    def get_lmps():
        lmps = serializer.get_lmps()
        return lmps

    @app.get('/api/lmps/search')
    def search_lmps(q: str = Query(...)):
        lmps = serializer.search_lmps(q)
        return lmps

    @app.get('/api/lmps/{lmp_id}')
    def get_lmp(lmp_id: str):
        lmps = serializer.get_lmps(lmp_id=lmp_id)
        if lmps:
            return lmps[0]
        else:
            raise HTTPException(status_code=404, detail="LMP not found")

    @app.get('/api/invocations/{lmp_id}')
    def get_invocations(lmp_id: str):
        invocations = serializer.get_invocations(lmp_id)
        return invocations

    @app.post('/api/invocations/search')
    def search_invocations(q: str = Query(...)):
        invocations = serializer.search_invocations(q)
        return invocations

    @app.get('/api/lmps/{lmp_id}/versions')
    def get_lmp_versions(lmp_id: str):
        versions = serializer.get_lmp_versions(lmp_id)
        if versions:
            return versions
        else:
            raise HTTPException(status_code=404, detail="LMP versions not found")

    @app.get('/api/lmps/latest')
    async def get_latest_lmps():
        latest_lmps = serializer.get_latest_lmps()
        return latest_lmps

    return app