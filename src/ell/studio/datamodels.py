from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel
from ell.types import SerializedLMPBase, InvocationBase

class SerializedLMPPublic(SerializedLMPBase):
    pass
class SerializedLMPWithUses(SerializedLMPPublic):
    lmp_id : str
    uses: List["SerializedLMPPublic"]

class SerializedLMPCreate(SerializedLMPBase):
    pass

class SerializedLMPUpdate(SQLModel):
    name: Optional[str] = None
    source: Optional[str] = None
    dependencies: Optional[str] = None
    is_lm: Optional[bool] = None
    api_params: Optional[Dict[str, Any]] = None
    initial_free_vars: Optional[Dict[str, Any]] = None
    initial_global_vars: Optional[Dict[str, Any]] = None
    commit_message: Optional[str] = None
    version_number: Optional[int] = None

class InvocationPublic(InvocationBase):
    lmp: SerializedLMPPublic
    consumes: List[str]
    consumed_by: List[str]
    uses: List[str]

class InvocationCreate(InvocationBase):
    pass

class InvocationUpdate(SQLModel):
    params: Optional[Dict[str, Any]] = None
    global_vars: Optional[Dict[str, Any]] = None
    free_vars: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    state_cache_key: Optional[str] = None
    invocation_api_params: Optional[Dict[str, Any]] = None


class SerializedLStrUpdate(SQLModel):
    content: Optional[str] = None
    logits: Optional[List[float]] = None

from pydantic import BaseModel

class GraphDataPoint(BaseModel):
    date: datetime
    count: int
    avg_latency: float
    tokens: int
    # cost: float

class InvocationsAggregate(BaseModel):
    total_invocations: int
    total_tokens: int
    avg_latency: float
    # total_cost: float
    unique_lmps: int
    # successful_invocations: int
    # success_rate: float
    graph_data: List[GraphDataPoint]