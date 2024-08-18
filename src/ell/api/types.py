from typing import Any, Dict, List,  Optional, Set, Tuple, cast
from datetime import datetime
from numpy import ndarray

from openai import BaseModel
from pydantic import AwareDatetime, Field
from ell.lstr import lstr

from ell.types import SerializedLMP, SerializedLStr, utc_now
import ell.types


class WriteLMPInput(BaseModel):
    """
    Arguments to write a LMP.
    """
    lmp_id: str
    name: str
    source: str
    dependencies: str
    is_lm: bool
    lm_kwargs: Optional[Dict[str, Any]] = None
    initial_free_vars: Optional[Dict[str, Any]] = None
    initial_global_vars: Optional[Dict[str, Any]] = None
    # num_invocations: Optional[int]
    commit_message: Optional[str] = None
    version_number: Optional[int] = None
    created_at:  Optional[AwareDatetime] = Field(default_factory=utc_now)

    def to_serialized_lmp(self):
        return SerializedLMP(
            lmp_id=self.lmp_id,
            name=self.name,
            source=self.source,
            dependencies=self.dependencies,
            is_lm=self.is_lm,
            lm_kwargs=self.lm_kwargs,
            version_number=self.version_number,
            initial_global_vars=self.initial_global_vars,
            initial_free_vars=self.initial_free_vars,
            commit_message=self.commit_message,
            created_at=cast(datetime, self.created_at)
        )


class LMP(BaseModel):
    lmp_id: str
    name: str
    source: str
    dependencies: str
    is_lm: bool
    lm_kwargs: Optional[Dict[str, Any]]
    initial_free_vars: Optional[Dict[str, Any]]
    initial_global_vars: Optional[Dict[str, Any]]
    created_at: AwareDatetime
    version_number: int
    commit_message: Optional[str]
    num_invocations: int

    @staticmethod
    def from_serialized_lmp(serialized: SerializedLMP):
        return LMP(
            lmp_id=cast(str, serialized.lmp_id),
            name=serialized.name,
            source=serialized.source,
            dependencies=serialized.dependencies,
            is_lm=serialized.is_lm,
            lm_kwargs=serialized.lm_kwargs,
            initial_free_vars=serialized.initial_free_vars,
            initial_global_vars=serialized.initial_global_vars,
            created_at=serialized.created_at,
            version_number=cast(int, serialized.version_number),
            commit_message=serialized.commit_message,
            num_invocations=cast(int, serialized.num_invocations),
        )

# class GetLMPResponse(BaseModel):
#     lmp: LMP
#     uses: List[str]


GetLMPResponse = Optional[LMP]
# class LMPCreatedEvent(BaseModel):
#     lmp: LMP
#     uses: List[str]


class Invocation(BaseModel):
    """
    An invocation of an LMP.
    """
    id: Optional[str] = None
    lmp_id: str
    args: List[Any]
    kwargs: Dict[str, Any]
    global_vars: Dict[str, Any]
    free_vars: Dict[str, Any]
    latency_ms: int
    invocation_kwargs: Dict[str, Any]
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    state_cache: Optional[str] = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    # used_by_id: Optional[str] = None

    def to_serialized_invocation(self):
        return ell.types.Invocation(
            **self.model_dump()
        )


class WriteInvocationInputLStr(BaseModel):
    id: Optional[str] = None
    content: str
    logits: Optional[List[float]] = None


def lstr_to_serialized_lstr(ls: lstr) -> SerializedLStr:
    return SerializedLStr(
        content=str(ls),
        logits=ls.logits if ls.logits is not None else None
    )


class WriteInvocationInput(BaseModel):
    """
    Arguments to write an invocation.
    """
    invocation: Invocation
    results: List[WriteInvocationInputLStr]
    consumes: List[str]

    def to_serialized_invocation_input(self) -> Tuple[ell.types.Invocation, List[SerializedLStr], List[str]]:
        results = [
            SerializedLStr(
                id=ls.id,
                content=ls.content,
                logits=ndarray(
                    ls.logits) if ls.logits is not None else None
            )
            for ls in self.results]

        sinvo = self.invocation.to_serialized_invocation()
        return  sinvo, results, self.consumes

class LMPInvokedEvent(BaseModel):
    lmp_id: str
    # invocation_id: str
    results: List[SerializedLStr]
    consumes: List[str]
