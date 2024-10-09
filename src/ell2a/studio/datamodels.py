from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel
from ell2a.types import SerializedLMPBase, InvocationBase, InvocationContentsBase


class SerializedLMPWithUses(SerializedLMPBase):
    lmp_id: str
    uses: List[SerializedLMPBase]


class InvocationPublic(InvocationBase):
    lmp: SerializedLMPBase
    uses: List["InvocationPublicWithConsumes"]
    contents: InvocationContentsBase


class InvocationPublicWithConsumes(InvocationPublic):
    consumes: List[InvocationPublic]
    consumed_by: List[InvocationPublic]


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
