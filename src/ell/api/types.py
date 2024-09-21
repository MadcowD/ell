from functools import cached_property
from typing import Any, Dict, List,  Optional, Tuple, Union, cast
from datetime import datetime, timezone
import uuid

from openai import BaseModel
from pydantic import AwareDatetime, Field

import ell.sqlmodels
from ell.types.message import Message
from ell.types.lmp import LMPType


def utc_now() -> datetime:
    """
    Returns the current UTC timestamp.
    Serializes to ISO-8601.
    """
    return datetime.now(tz=timezone.utc)


class WriteLMPInput(BaseModel):
    """
    Arguments to write a LMP.
    """
    lmp_id: str
    name: str
    source: str
    dependencies: str
    lmp_type: LMPType
    api_params: Optional[Dict[str, Any]] = None
    initial_free_vars: Optional[Dict[str, Any]] = None
    initial_global_vars: Optional[Dict[str, Any]] = None

    # this is omitted so as to not confuse whether the number should be incremented (should always happen at the db level)
    # num_invocations: Optional[int] = None
    commit_message: Optional[str] = None
    version_number: Optional[int] = None
    created_at:  Optional[AwareDatetime] = Field(default_factory=utc_now)

    def to_serialized_lmp(self):
        return ell.sqlmodels.SerializedLMP(
            lmp_id=self.lmp_id,
            lmp_type=self.lmp_type,
            name=self.name,
            source=self.source,
            dependencies=self.dependencies,
            api_params=self.api_params,
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
    lmp_type: LMPType
    api_params: Optional[Dict[str, Any]]
    initial_free_vars: Optional[Dict[str, Any]]
    initial_global_vars: Optional[Dict[str, Any]]
    created_at: AwareDatetime
    version_number: int
    commit_message: Optional[str]
    num_invocations: int

    @staticmethod
    def from_serialized_lmp(serialized: ell.sqlmodels.SerializedLMP):
        return LMP(
            lmp_id=cast(str, serialized.lmp_id),
            name=serialized.name,
            source=serialized.source,
            dependencies=serialized.dependencies,
            lmp_type=serialized.lmp_type,
            api_params=serialized.api_params,
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

InvocationResults = Union[List[Message], Any]


class InvocationContents(BaseModel):
    invocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    params: Optional[Dict[str, Any]] = None
    results: Optional[InvocationResults] = None
    invocation_api_params: Optional[Dict[str, Any]] = None
    global_vars: Optional[Dict[str, Any]] = None
    free_vars: Optional[Dict[str, Any]] = None
    is_external: bool = Field(default=False)

    def to_serialized_invocation_contents(self):
        return ell.sqlmodels.InvocationContents(
            **self.model_dump()
        )

    @cached_property
    def total_size_bytes(self) -> int:
        """
        Returns the total uncompressed size of the invocation contents as JSON in bytes.
        """
        import json
        json_fields = [
            self.params,
            self.results,
            self.invocation_api_params,
            self.global_vars,
            self.free_vars
        ]
        return sum(len(json.dumps(field, default=(lambda x: x.model_dump_json() if isinstance(x, BaseModel) else str(x))).encode('utf-8')) for field in json_fields if field is not None)

    @cached_property
    def should_externalize(self) -> bool:
        return self.total_size_bytes > 102400  # Precisely 100kb in bytes


class Invocation(BaseModel):
    """
    An invocation of an LMP.
    """
    id: Optional[str] = None
    lmp_id: str
    latency_ms: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    state_cache_key: Optional[str] = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    used_by_id: Optional[str] = None
    contents: InvocationContents

    def to_serialized_invocation(self):
        return ell.sqlmodels.Invocation(
            **self.model_dump(exclude={"contents"}),
            contents=self.contents.to_serialized_invocation_contents()
        )


class WriteInvocationInput(BaseModel):
    """
    Arguments to write an invocation.
    """
    invocation: Invocation
    consumes: List[str]

    def to_serialized_invocation_input(self) -> Tuple[ell.sqlmodels.Invocation, List[str]]:
        sinvo = self.invocation.to_serialized_invocation()
        return sinvo, list(set(self.consumes))


class LMPInvokedEvent(BaseModel):
    lmp_id: str
    # invocation_id: str
    consumes: List[str]
