import uuid
from datetime import datetime, timezone
from functools import cached_property
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, AwareDatetime, Field, field_serializer, field_validator

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
    # TODO. dict or list?
    # uses: List[str] = Field(default_factory=list)

    # this is omitted so as to not confuse whether the number should be incremented (should always happen at the db level)
    # num_invocations: Optional[int] = None
    commit_message: Optional[str] = None
    version_number: Optional[int] = None
    created_at: Optional[AwareDatetime] = Field(default_factory=utc_now)


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


class GetLMPInput(BaseModel):
    id: str


GetLMPOutput = Optional[LMP]


class InvocationContents(BaseModel):
    invocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID of the invocation the contents belong to")
    params: Optional[Dict[str, Any]] = Field(description="The parameters of the LMP at the time of the invocation", default=None)
    results: Optional[List[Message]] = Field(description="The output of the invocation as a list of ell Messages", default=None)
    invocation_api_params: Optional[Dict[str, Any]] = Field(description="Arguments the model API was called with", default=None)
    global_vars: Optional[Dict[str, Any]] = Field(description="Global variable bindings and their values at the time of the invocation", default=None)
    free_vars: Optional[Dict[str, Any]] = Field(description="Free variable bindings and their values at the time of the invocation", default=None)
    is_external: bool = Field(default=False, description="Whether the invocation contents are stored externally in a blob store. If they are they can be retrieved by 'invocation-{invocation_id}'.")

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
        # todo(alex): we may want to bring this in line with other json serialization
        return sum(
            len(json.dumps(field, default=(lambda x: json.dumps(x.model_dump(), default=str, ensure_ascii=False)
                                           if isinstance(x, BaseModel) else str(x)), ensure_ascii=False).encode('utf-8'))
            for field in json_fields if field is not None
        )

    @cached_property
    def should_externalize(self) -> bool:
        return self.total_size_bytes > 102400  # Precisely 100kb in bytes


class Invocation(BaseModel):
    """
    An invocation of an LMP.
    """
    id: Optional[str] = None
    lmp_id: str
    latency_ms: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    state_cache_key: Optional[str] = None
    created_at: AwareDatetime = Field(default_factory=utc_now)
    used_by_id: Optional[str] = None
    contents: InvocationContents

    # Note: we must set to always right now, because the global json serializer calls model_dump instead of
    # model_dump_json and then json.dumps with default of repr. would prefer when_used=json but
    # tbh it's probably not needed as i think pydantic already handles this for json

    @field_serializer('created_at', when_used='always')
    def serialize_date(self, created_at: AwareDatetime):
        return str(created_at)

    @field_validator('created_at', mode="before")
    def deserialize_and_validate_date(cls, created_at: Union[str, AwareDatetime]):
        if isinstance(created_at, str):
            dt = datetime.fromisoformat(created_at)
            if dt.tzinfo is None:
                raise ValueError(
                    "Datetime string must include timezone information")
            return dt
        return created_at


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


class WriteBlobInput(BaseModel):
    """
    Arguments to write a blob to a blob store
    """
    blob_id: str
    blob: bytes
    metadata: Optional[Dict[str, Any]] = None


# class Blob(BaseModel):
#     blob_id: str
#     blob: bytes
#     content_type: str
#     metadata: Optional[Dict[str, Any]] = None
#
#     @cached_property
#     def size_bytes(self) -> int:
#         return len(self.blob)
#
#
