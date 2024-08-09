from datetime import datetime
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import cattrs
import numpy as np
from sqlalchemy.sql import text
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr, utc_now
from ell.lstr import lstr
from sqlalchemy import or_, func, and_

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)
        

        self.open_files: Dict[str, Dict[str, Any]] = {}


    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        with Session(self.engine) as session:
            # Bind the serialized_lmp to the session
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == serialized_lmp.lmp_id).first()
            
            if lmp:
                # Already added to the DB.
                return lmp
            else:
                session.add(serialized_lmp)
            
            for use_id in uses:
                used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()
                if used_lmp:
                    serialized_lmp.uses.append(used_lmp)
            
            session.commit()
        return None

    def write_invocation(self, invocation: Invocation, results: List[SerializedLStr], consumes: Set[str]) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == invocation.lmp_id).first()
            assert lmp is not None, f"LMP with id {invocation.lmp_id} not found. Writing invocation erroneously"
            
            # Increment num_invocations
            if lmp.num_invocations is None:
                lmp.num_invocations = 1
            else:
                lmp.num_invocations += 1

            session.add(invocation)

            for result in results:
                result.producer_invocation = invocation
                session.add(result)

            # Now create traces.
            for consumed_id in consumes:
                session.add(InvocationTrace(
                    invocation_consumer_id=invocation.id,
                    invocation_consuming_id=consumed_id
                ))

            session.commit()
            return None
        
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
        def fetch_invocation(inv_id):
            query = (
                select(Invocation, SerializedLStr, SerializedLMP)
                .join(SerializedLMP)
                .outerjoin(SerializedLStr)
                .where(Invocation.id == inv_id)
            )
            results = session.exec(query).all()

            if not results:
                return None

            inv, lstr, lmp = results[0]
            inv_dict = inv.model_dump()
            inv_dict['lmp'] = lmp.model_dump()
            inv_dict['results'] = [dict(**l.model_dump(), __lstr=True) for l in [r[1] for r in results if r[1]]]

            # Fetch consumes and consumed_by invocation IDs
            consumes_query = select(InvocationTrace.invocation_consuming_id).where(InvocationTrace.invocation_consumer_id == inv_id)
            consumed_by_query = select(InvocationTrace.invocation_consumer_id).where(InvocationTrace.invocation_consuming_id == inv_id)

            inv_dict['consumes'] = [r for r in session.exec(consumes_query).all()]
            inv_dict['consumed_by'] = [r for r in session.exec(consumed_by_query).all()]
            inv_dict['uses'] = list([d.id for d in inv.uses]) 


            return inv_dict

        query = select(Invocation.id).join(SerializedLMP)

        # Apply LMP filters
        for key, value in lmp_filters.items():
            query = query.where(getattr(SerializedLMP, key) == value)

        # Apply invocation filters
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(Invocation, key) == value)

        # Sort from newest to oldest
        query = query.order_by(Invocation.created_at.desc()).offset(skip).limit(limit)

        invocation_ids = session.exec(query).all()

        invocations = [fetch_invocation(inv_id) for inv_id in invocation_ids if inv_id]

        if hierarchical:
            # Fetch all related "uses" invocations
            used_ids = set()
            for inv in invocations:
                
                used_ids.update(inv['uses'])

            used_invocations = [fetch_invocation(inv_id) for inv_id in used_ids if inv_id not in invocation_ids]
            invocations.extend(used_invocations)

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
        

    def get_all_traces_leading_to(self, session: Session, invocation_id: str) -> List[Dict[str, Any]]:

        traces = []
        visited = set()
        queue = [(invocation_id, 0)]

        while queue:
            current_invocation_id, depth = queue.pop(0)
            if depth > 4:
                continue

            if current_invocation_id in visited:
                continue

            visited.add(current_invocation_id)

            results = session.exec(
                select(InvocationTrace, Invocation, SerializedLMP)
                .join(Invocation, InvocationTrace.invocation_consuming_id == Invocation.id)
                .join(SerializedLMP, Invocation.lmp_id == SerializedLMP.lmp_id)
                .where(InvocationTrace.invocation_consumer_id == current_invocation_id)
            ).all()
            for row in results:
                trace = {
                    'consumer_id': row.InvocationTrace.invocation_consumer_id,
                    'consumed': {key: value for key, value in row.Invocation.__dict__.items() if key not in ['invocation_consumer_id', 'invocation_consuming_id']},
                    'consumed_lmp': row.SerializedLMP.model_dump()
                }
                traces.append(trace)
                queue.append((row.Invocation.id, depth + 1))
                
        # Create a dictionary to store unique traces based on consumed.id
        unique_traces = {}
        for trace in traces:
            consumed_id = trace['consumed']['id']
            if consumed_id not in unique_traces:
                unique_traces[consumed_id] = trace
        
        # Convert the dictionary values back to a list
        return list(unique_traces.values())


class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}')