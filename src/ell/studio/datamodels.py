from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel
from ell.stores.models.evaluations import (
    EvaluationLabelBase,
    EvaluationLabelerBase,
    SerializedEvaluationBase,
    SerializedEvaluationRunBase,
    EvaluationRunLabelerSummaryBase,
    EvaluationResultDatapointBase,
)
from ell.stores.models.core import SerializedLMPBase, InvocationBase, InvocationContentsBase


class SerializedLMPWithUses(SerializedLMPBase):
    lmp_id : str
    uses: List[SerializedLMPBase]


class InvocationPublic(InvocationBase):
    lmp: SerializedLMPBase
    uses: List["InvocationPublicWithConsumes"] 
    contents: InvocationContentsBase

class InvocationPublicWithConsumes(InvocationPublic):
    consumes: List[InvocationPublic]
    consumed_by: List[InvocationPublic]


class InvocationPublicWithoutLMP(InvocationBase):
    uses : List["InvocationPublicWithoutLMPAndConsumes"]
    contents: InvocationContentsBase


class InvocationPublicWithoutLMPAndConsumes(InvocationPublicWithoutLMP):
    consumes: List[InvocationPublicWithoutLMP]
    consumed_by: List[InvocationPublicWithoutLMP]


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


# Update these models at the end of the file
class EvaluationLabelerPublic(EvaluationLabelerBase):
    labeling_lmp: Optional[SerializedLMPBase]

class EvaluationRunLabelerSummaryPublic(EvaluationRunLabelerSummaryBase):
    evaluation_labeler: EvaluationLabelerPublic

class EvaluationRunPublic(SerializedEvaluationRunBase):
    evaluated_lmp: SerializedLMPBase
    labeler_summaries: List[EvaluationRunLabelerSummaryPublic]

class EvaluationPublic(SerializedEvaluationBase):
    labelers: List[EvaluationLabelerPublic]
    runs: List[EvaluationRunPublic]

# XXXX
class EvaluationPublicWithoutRuns(SerializedEvaluationBase):
    labelers: List[EvaluationLabelerPublic]

# XXXXXX
class EvaluationLabelPublic(EvaluationLabelBase):
    label_invocation: Optional[InvocationPublicWithoutLMP]
    labeler : EvaluationLabelerBase

class EvaluationResultDatapointPublic(EvaluationResultDatapointBase):
    invocation_being_labeled: InvocationPublicWithoutLMP
    labels: List[EvaluationLabelPublic]

class SpecificEvaluationRunPublic(SerializedEvaluationRunBase):
    evaluated_lmp: SerializedLMPBase
    evaluation: EvaluationPublicWithoutRuns
    labeler_summaries: List[EvaluationRunLabelerSummaryPublic]
