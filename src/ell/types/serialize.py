import uuid
from datetime import datetime, timezone
from functools import cached_property
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, AwareDatetime, Field

from ell.types.lmp import LMPType
from ell.types.message import Message


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


GetLMPResponse = Optional[LMP]

InvocationResults = Union[List[Message], Any]


class InvocationContents(BaseModel):
    invocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    params: Optional[Dict[str, Any]] = None
    results: Optional[InvocationResults] = None
    invocation_api_params: Optional[Dict[str, Any]] = None
    global_vars: Optional[Dict[str, Any]] = None
    free_vars: Optional[Dict[str, Any]] = None
    is_external: bool = Field(default=False)

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


class WriteInvocationInput(BaseModel):
    """
    Arguments to write an invocation.
    """
    invocation: Invocation
    consumes: List[str]


class LMPInvokedEvent(BaseModel):
    lmp_id: str
    # invocation_id: str
    consumes: List[str]
