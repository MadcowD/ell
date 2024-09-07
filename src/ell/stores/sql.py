from datetime import datetime, timedelta
import json
import os
from typing import Any, Optional, Dict, List, Set
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
from sqlalchemy.sql import text
from ell.types import InvocationTrace, SerializedLMP, Invocation
from sqlalchemy import func, and_
from ell.types.studio import utc_now
from ell.util.serialization import pydantic_ltype_aware_cattr
import gzip
import logging
from typing import Any, Optional, Dict, List, Set
from datetime import datetime, timedelta
from sqlalchemy import Engine, func, and_

logger = logging.getLogger(__name__)

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: Optional[str] = None, blob_store: Optional[ell.store.BlobStore] = None, engine: Optional[Engine] = None):

        if engine is not None:
            self.engine = engine
        elif db_uri is None:
            raise ValueError(
                "db_uri cannot be None when engine is not provided as an argument")
        else:
            self.engine = create_engine(
                db_uri,
                json_serializer=lambda obj: json.dumps(pydantic_ltype_aware_cattr.unstructure(obj),
                                                       sort_keys=True, default=repr))
        SQLModel.metadata.create_all(self.engine)
        super().__init__(blob_store)

    def get_lmp(self, lmp_id: str, session: Optional[Session] = None) -> Optional[SerializedLMP]:
        if session is None:
            with Session(self.engine) as session:
                return session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == lmp_id)).first()
        else:
            return session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == lmp_id)).first()

    def write_lmp(self, serialized_lmp: SerializedLMP, uses: List[str]) -> Optional[Any]:
        """
        Creates an LMP if it does not exist.
        LMPs as entities are not unique by fqn but by lmp_id. 
        """
        with Session(self.engine) as session:
            logger.debug(f"Begin writing LMP {serialized_lmp.lmp_id}")
            # Bind the serialized_lmp to the session
            lmp = None
            if serialized_lmp.lmp_id:
                lmp = self.get_lmp(serialized_lmp.lmp_id, session)

            if lmp:
                # Already added to the DB.
                logger.debug(f"LMP {serialized_lmp.lmp_id} already exists in the DB. Skipping write.")
                return lmp
            else:
                session.add(serialized_lmp)
            
            for use_id in uses:
                used_lmp = self.get_lmp(use_id, session)
                if used_lmp:
                    serialized_lmp.uses.append(used_lmp)
            
            session.commit()
            logger.debug(f"Wrote new LMP {serialized_lmp.lmp_id} to the DB.")
        return None

    def write_invocation(self, invocation: Invocation, consumes: Set[str]) -> Optional[Any]:
        with Session(self.engine) as session:
            logger.debug(f"Begin writing invocation {invocation.id}")
            lmp = self.get_lmp(invocation.lmp_id, session)
            assert lmp is not None, f"LMP with id {invocation.lmp_id} not found. Writing invocation erroneously"
            
            # Increment num_invocations
            if lmp.num_invocations is None:
                lmp.num_invocations = 1
            else:
                lmp.num_invocations += 1

            # Add the invocation contents
            session.add(invocation.contents)

            # Add the invocation
            session.add(invocation)

            logger.debug(f"Committing invocation {invocation.id}")
            session.commit()
            logger.debug(f"Committed invocation {invocation.id}")

            # Now create traces.
            for consumed_id in consumes:
                logger.debug(f"Creating trace from {invocation.id} to {consumed_id}")
                session.add(InvocationTrace(
                    invocation_consumer_id=invocation.id,
                    invocation_consuming_id=consumed_id
                ))

            logger.debug(f"Committing traces for invocation {invocation.id}")
            session.commit()
            logger.debug(f"Committed traces for invocation {invocation.id}")
            return invocation
        
    def get_cached_invocations(self, lmp_id :str, state_cache_key :str) -> List[Invocation]:
        with Session(self.engine) as session:
            return self.get_invocations(session, lmp_filters={"lmp_id": lmp_id}, filters={"state_cache_key": state_cache_key})
        
    def get_versions_by_fqn(self, fqn :str) -> List[SerializedLMP]:
        with Session(self.engine) as session:
            return self.get_lmps(session, name=fqn)
        
    ## HELPER METHODS FOR ELL STUDIO! :) 
    def get_latest_lmps(self, session: Session, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Gets all the lmps grouped by unique name with the highest created at
        """
        subquery = (
            select(SerializedLMP.name, func.max(SerializedLMP.created_at).label("max_created_at"))
            .group_by(SerializedLMP.name)
            .subquery()
        )
        
        filters = {
            "name": subquery.c.name,
            "created_at": subquery.c.max_created_at
        }
        
        return self.get_lmps(session, skip=skip, limit=limit, subquery=subquery, **filters)

        
    def get_lmps(self, session: Session, skip: int = 0, limit: int = 10, subquery=None, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:

        query = select(SerializedLMP)
        
        if subquery is not None:
            query = query.join(subquery, and_(
                SerializedLMP.name == subquery.c.name,
                SerializedLMP.created_at == subquery.c.max_created_at
            ))
        
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(SerializedLMP, key) == value)
        
        query = query.order_by(SerializedLMP.created_at.desc())  # Sort by created_at in descending order
        query = query.offset(skip).limit(limit)
        results = session.exec(query).all()
        
        return results

    def get_invocations(self, session: Session, lmp_filters: Dict[str, Any], skip: int = 0, limit: int = 10, filters: Optional[Dict[str, Any]] = None, hierarchical: bool = False) -> List[Dict[str, Any]]:

        query = select(Invocation).join(SerializedLMP)

        # Apply LMP filters
        for key, value in lmp_filters.items():
            query = query.where(getattr(SerializedLMP, key) == value)

        # Apply invocation filters
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(Invocation, key) == value)

        # Sort from newest to oldest
        query = query.order_by(Invocation.created_at.desc()).offset(skip).limit(limit)

        invocations = session.exec(query).all()
        return invocations


    def get_traces(self, session: Session):
        query = text("""
        SELECT 
            consumer.lmp_id, 
            trace.*, 
            consumed.lmp_id
        FROM 
            invocation AS consumer
        JOIN 
            invocationtrace AS trace ON consumer.id = trace.invocation_consumer_id
        JOIN 
            invocation AS consumed ON trace.invocation_consuming_id = consumed.id
        """)
        results = session.exec(query).all()
        
        traces = []
        for (consumer_lmp_id, consumer_invocation_id, consumed_invocation_id, consumed_lmp_id) in results:
            traces.append({
                'consumer': consumer_lmp_id,
                'consumed': consumed_lmp_id
            })
        
        return traces

    def get_invocations_aggregate(self, session: Session, lmp_filters: Dict[str, Any] = None, filters: Dict[str, Any] = None, days: int = 30) -> Dict[str, Any]:
        # Calculate the start date for the graph data
        start_date = datetime.utcnow() - timedelta(days=days)

        # Base subquery
        base_subquery = (
            select(Invocation.created_at, Invocation.latency_ms, Invocation.prompt_tokens, Invocation.completion_tokens, Invocation.lmp_id)
            .join(SerializedLMP, Invocation.lmp_id == SerializedLMP.lmp_id)
            .filter(Invocation.created_at >= start_date)
        )

        # Apply filters
        if lmp_filters:
            base_subquery = base_subquery.filter(and_(*[getattr(SerializedLMP, k) == v for k, v in lmp_filters.items()]))
        if filters:
            base_subquery = base_subquery.filter(and_(*[getattr(Invocation, k) == v for k, v in filters.items()]))


        data = session.exec(base_subquery).all()

        # Calculate aggregate metrics
        total_invocations = len(data)
        total_tokens = sum(row.prompt_tokens + row.completion_tokens for row in data)
        avg_latency = sum(row.latency_ms for row in data) / total_invocations if total_invocations > 0 else 0
        unique_lmps = len(set(row.lmp_id for row in data))

        # Prepare graph data
        graph_data = []
        for row in data:
            graph_data.append({
                "date": row.created_at,
                "avg_latency": row.latency_ms,
                "tokens": row.prompt_tokens + row.completion_tokens,
                "count": 1
            })

        return {
            "total_invocations": total_invocations,
            "total_tokens": total_tokens,
            "avg_latency": avg_latency,
            "unique_lmps": unique_lmps,
            "graph_data": graph_data
        }


class SQLiteStore(SQLStore):
    def __init__(self, db_dir: str):
        assert not db_dir.endswith('.db'), "Create store with a directory not a db."
        if ":memory:" not in db_dir:
            os.makedirs(db_dir, exist_ok=True)
            self.db_dir = db_dir
            db_path = os.path.join(db_dir, 'ell.db')
            blob_store = SQLBlobStore(db_dir)
            super().__init__(f'sqlite:///{db_path}', blob_store=blob_store)
        else:
            from sqlalchemy.pool import StaticPool
            # todo. set up blob store for in-memory
            engine = create_engine(
                'sqlite://',
                connect_args={'check_same_thread': False},
                poolclass=StaticPool
            )

            return super().__init__(engine=engine)


    def write_external_blob(self, id: str, json_dump: str, depth: int = 2):
        assert self.blob_store is not None, "Blob store is not initialized"
        self.blob_store.store_blob(json_dump.encode('utf-8'), metadata={'id': id, 'depth': depth})

    def read_external_blob(self, id: str, depth: int = 2) -> str:
        assert self.blob_store is not None, "Blob store is not initialized"
        return self.blob_store.retrieve_blob(id).decode('utf-8')

# todo. rename to sqlite blob store or local fs blob store
class SQLBlobStore(ell.store.BlobStore):
    def __init__(self, db_dir: str):
        self.db_dir = db_dir

    def store_blob(self, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        blob_id = f"blob-{utc_now().isoformat()}"
        file_path = self._get_blob_path(blob_id)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with gzip.open(file_path, "wb") as f:
            f.write(blob)
        return blob_id

    def retrieve_blob(self, blob_id: str) -> bytes:
        file_path = self._get_blob_path(blob_id)
        with gzip.open(file_path, "rb") as f:
            return f.read()

    def _get_blob_path(self, id: str, depth: int = 2) -> str:
        assert "-" in id, "Blob id must have a single - in it to split on."
        _type, _id = id.split("-")
        increment = 2
        dirs = [_type] + [_id[i:i+increment] for i in range(0, depth*increment, increment)]
        file_name = _id[depth*increment:]
        return os.path.join(self.db_dir, "blob", *dirs, file_name)

# i think we should consider for multimedia inputs
# having the image available at a url ahead of time (ie don't call the llm with base64)
# to reduce transactional issues later
# it's recommended to use image urls for long running conversations anyway
# suppodely it's generally bad to store blobs in postgres so i'm not sure i'll implement this
class PostgresBlobStore(ell.store.BlobStore):
    """
    Blob store that uses postgres as the backing store.
    Not recommended for production use.

    """
    def __init__(self, db_uri: str):
        self.db_uri = db_uri
        raise NotImplementedError("Not implemented")

    def store_blob(self, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        raise NotImplementedError("Not implemented")

    def retrieve_blob(self, blob_id: str) -> bytes:
        raise NotImplementedError("Not implemented")

class PostgresStore(SQLStore):
    def __init__(self, db_uri: str, blob_store: Optional[ell.store.BlobStore] = None):
        super().__init__(db_uri )
        if blob_store is not None:
            self.blob_store = blob_store
        else:
            logger.warning("No blob store provided.")
            # raise NotImplementedError("Not implemented")
            # self.blob_store = PostgresBlobStore(db_uri)
