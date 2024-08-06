import datetime
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import cattrs
import numpy as np
from sqlalchemy.sql import text
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr
from ell.lstr import lstr
from sqlalchemy import or_, func, and_

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)
        

        self.open_files: Dict[str, Dict[str, Any]] = {}


    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str, 
                  version_number: int,
                  uses: Dict[str, Any], 
                  global_vars: Dict[str, Any],
                  free_vars: Dict[str, Any],
                  commit_message: Optional[str] = None,
                  created_at: Optional[float]=None) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()
            
            if lmp:
                # Already added to the DB.
                return lmp
            else:
                lmp = SerializedLMP(
                    lmp_id=lmp_id,
                    name=name,
                    version_number=version_number,
                    source=source,
                    dependencies=dependencies,
                    initial_global_vars=global_vars,
                    initial_free_vars=free_vars,
                    created_at= created_at or datetime.datetime.utcnow(),
                    is_lm=is_lmp,
                    lm_kwargs=lm_kwargs,
                    commit_message=commit_message
                )
                session.add(lmp)
            
            for use_id in uses:
                used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()
                if used_lmp:
                    lmp.uses.append(used_lmp)
            
            session.commit()
        return None

    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any],  
                         global_vars: Dict[str, Any],
                         free_vars: Dict[str, Any], created_at: Optional[float], consumes: Set[str], prompt_tokens: Optional[int] = None,
                         completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,
                         state_cache_key: Optional[str] = None,
                         cost_estimate: Optional[float] = None) -> Optional[Any]:
        with Session(self.engine) as session:
            if isinstance(result, lstr):
                results = [result]
            elif isinstance(result, list):
                results = result
            else:
                raise TypeError("Result must be either lstr or List[lstr]")

            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()
            assert lmp is not None, f"LMP with id {lmp_id} not found. Writing invocation erroneously"
            
            # Increment num_invocations
            if lmp.num_invocations is None:
                lmp.num_invocations = 1
            else:
                lmp.num_invocations += 1
            invocation = Invocation(
                id=id,
                lmp_id=lmp.lmp_id,
                args=args,
                kwargs=kwargs,
                global_vars=json.loads(json.dumps(global_vars, default=str)),
                free_vars=json.loads(json.dumps(free_vars, default=str)),
                created_at=created_at,
                invocation_kwargs=invocation_kwargs,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                state_cache_key=state_cache_key,
            )

            for res in results:
                serialized_lstr = SerializedLStr(content=str(res), logits=res.logits)
                session.add(serialized_lstr)
                invocation.results.append(serialized_lstr)
            
            session.add(invocation)

            # Now create traces.
            for consumed_id in consumes:
                session.add(InvocationTrace(
                    invocation_consumer_id=id,
                    invocation_consuming_id=consumed_id
                ))

            session.commit()
    
    def get_latest_lmps(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
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
        
        return self.get_lmps(skip=skip, limit=limit, subquery=subquery, **filters)

    def get_lmps(self, skip: int = 0, limit: int = 10, subquery=None, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(SerializedLMP, SerializedLMPUses.lmp_user_id).outerjoin(
                SerializedLMPUses,
                SerializedLMP.lmp_id == SerializedLMPUses.lmp_using_id
            )
            
            if subquery is not None:
                query = query.join(subquery, and_(
                    SerializedLMP.name == subquery.c.name,
                    SerializedLMP.created_at == subquery.c.max_created_at
                ))
            
            if filters:
                print(f"Filters: {filters}")
                for key, value in filters.items():
                    query = query.where(getattr(SerializedLMP, key) == value)
            
            query = query.order_by(SerializedLMP.created_at.desc())  # Sort by created_at in descending order
            query = query.offset(skip).limit(limit)
            results = session.exec(query).all()
            
            lmp_dict = {lmp.lmp_id: {**lmp.model_dump(), 'uses': []} for lmp, _ in results}
            for lmp, using_id in results:
                if using_id:
                    lmp_dict[lmp.lmp_id]['uses'].append(using_id)
            return list(lmp_dict.values())

    def get_invocations(self, lmp_filters: Dict[str, Any], skip: int = 0, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(Invocation, SerializedLStr, SerializedLMP).join(SerializedLMP).outerjoin(SerializedLStr)
            
            # Apply LMP filters
            for key, value in lmp_filters.items():
                query = query.where(getattr(SerializedLMP, key) == value)
            
            # Apply invocation filters
            if filters:
                for key, value in filters.items():
                    query = query.where(getattr(Invocation, key) == value)
            
            # Sort from newest to oldest
            query = query.order_by(Invocation.created_at.desc()).offset(skip).limit(limit)
            
            results = session.exec(query).all()
            
            invocations = {}
            for inv, lstr, lmp in results:
                if inv.id not in invocations:
                    inv_dict = inv.model_dump()
                    inv_dict['lmp'] = lmp.model_dump()
                    invocations[inv.id] = inv_dict
                    invocations[inv.id]['results'] = []
                if lstr:
                    invocations[inv.id]['results'].append(dict(**lstr.model_dump(), __lstr=True))
            
            return list(invocations.values())

    def get_traces(self):
        with Session(self.engine) as session:
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
        

    def get_all_traces_leading_to(self, invocation_id: str) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
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