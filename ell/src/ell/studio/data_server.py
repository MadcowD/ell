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


    
    @app.get('/api/lmps/{name:path}')
    def get_lmp(name: str):
        # Remove any leading slash if present
        name = name.lstrip('/')
        
        # First, try to get by name
        lmps_by_name = serializer.get_lmps(name=name)
        if lmps_by_name:
            return list(lmps_by_name)        
        # If not found by name, check if the last part of the path is a valid lmp_id
        name_parts = name.split('/')
        if len(name_parts) > 1:
            potential_lmp_id = name_parts[-1]
            potential_name = '/'.join(name_parts[:-1])
            lmps = serializer.get_lmps(name=potential_name, lmp_id=potential_lmp_id)
            if lmps:
                return list(lmps)

        raise HTTPException(status_code=404, detail="LMP not found")
    

    @app.get('/api/invocations/{name:path}')
    def get_invocations(name: str):
        name = name.lstrip('/')
        name_parts = name.split('/')

        lmp_filters = {"name": name_parts[0]}
        if len(name_parts) > 1: 
            potential_lmp_id = name_parts[-1]
            lmp_filters["lmp_id"] = potential_lmp_id
            
            
        invocations = serializer.get_invocations(lmp_filters=lmp_filters)
        return invocations

    @app.post('/api/invocations/search')
    def search_invocations(q: str = Query(...)):
        invocations = serializer.search_invocations(q)
        return invocations

    return app