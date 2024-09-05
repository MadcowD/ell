from datetime import datetime, timezone
import enum
from functools import cached_property

import sqlalchemy.types as types

from ell.types.message import Any, Any, Field, Message, Optional

from sqlmodel import Column, Field, SQLModel
from typing import Optional
from dataclasses import dataclass
from typing import Dict, List, Literal, Union, Any, Optional

from pydantic import BaseModel, field_validator

from datetime import datetime
from typing import Any, List, Optional
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from sqlalchemy import Index, func

from typing import TypeVar, Any

def utc_now() -> datetime:
    """
    Returns the current UTC timestamp.
    Serializes to ISO-8601.
    """
    return datetime.now(tz=timezone.utc)


class SerializedLMPUses(SQLModel, table=True):
    """
    Represents the many-to-many relationship between SerializedLMPs.

    This class is used to track which LMPs use or are used by other LMPs.
    """

    lmp_user_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)  # ID of the LMP that is being used
    lmp_using_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)  # ID of the LMP that is using the other LMP


class UTCTimestamp(types.TypeDecorator[datetime]):
    cache_ok = True
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect:Any):
        return value.replace(tzinfo=timezone.utc)


def UTCTimestampField(index:bool=False, **kwargs:Any):
    return Field(
        sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))


class LMPType(str, enum.Enum):
    LM = "LM"
    TOOL = "TOOL"
    MULTIMODAL = "MULTIMODAL"
    OTHER = "OTHER"



class SerializedLMPBase(SQLModel):
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    source: str
    dependencies: str
    created_at: datetime = UTCTimestampField(index=True, nullable=False)

    lmp_type: LMPType
    api_params: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    initial_free_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)


class SerializedLMP(SerializedLMPBase, table=True):
    invocations: List["Invocation"] = Relationship(back_populates="lmp")
    used_by: Optional[List["SerializedLMP"]] = Relationship(
        back_populates="uses",
        link_model=SerializedLMPUses,
        sa_relationship_kwargs=dict(
            primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id",
            secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id",
        ),
    )
    uses: List["SerializedLMP"] = Relationship(
        back_populates="used_by",
        link_model=SerializedLMPUses,
        sa_relationship_kwargs=dict(
            primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id",
            secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id",
        ),
    )

    class Config:
        table_name = "serializedlmp"
        unique_together = [("version_number", "name")]

class InvocationTrace(SQLModel, table=True):
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)

# Should be subtyped for differnet kidns of LMPS.
# XXX: Move all ofh te binary data out to a different table.
# XXX: Need a flag that says dont store images.
# XXX: Deprecate the args columns
class InvocationBase(SQLModel):
    id: Optional[str] = Field(default=None, primary_key=True)
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id", index=True)
    latency_ms: float
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    state_cache_key: Optional[str] = Field(default=None)
    created_at: datetime = UTCTimestampField(default=func.now(), nullable=False)
    used_by_id: Optional[str] = Field(default=None, foreign_key="invocation.id", index=True)
    # global_vars and free_vars removed from here

class InvocationContentsBase(SQLModel):
    invocation_id: str = Field(foreign_key="invocation.id", index=True, primary_key=True)
    params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    results: Optional[Union[List[Message], Any]] = Field(default=None, sa_column=Column(JSON))
    invocation_api_params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    global_vars: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    free_vars: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    is_external : bool = Field(default=False)

    @cached_property
    def should_externalize(self) -> bool:
        import json
        
        json_fields = [
            self.params,
            self.results,
            self.invocation_api_params,
            self.global_vars,
            self.free_vars
        ]
        
        total_size = sum(
            len(json.dumps(field, default=(lambda x: x.model_dump_json() if isinstance(x, BaseModel) else str(x))).encode('utf-8')) for field in json_fields if field is not None
        )
        # print("total_size", total_size)
        
        return total_size > 102400  # Precisely 100kb in bytes

class InvocationContents(InvocationContentsBase, table=True):
    invocation: "Invocation" = Relationship(back_populates="contents")

class Invocation(InvocationBase, table=True):
    lmp: SerializedLMP = Relationship(back_populates="invocations")
    consumed_by: List["Invocation"] = Relationship(
        back_populates="consumes",
        link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
        ),
    )
    consumes: List["Invocation"] = Relationship(
        back_populates="consumed_by",
        link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
        ),
    )
    used_by: Optional["Invocation"] = Relationship(back_populates="uses", sa_relationship_kwargs={"remote_side": "Invocation.id"})
    uses: List["Invocation"] = Relationship(back_populates="used_by")
    contents: InvocationContents = Relationship(back_populates="invocation")

    __table_args__ = (
        Index('ix_invocation_lmp_id_created_at', 'lmp_id', 'created_at'),
        Index('ix_invocation_created_at_latency_ms', 'created_at', 'latency_ms'),
        Index('ix_invocation_created_at_tokens', 'created_at', 'prompt_tokens', 'completion_tokens'),
    )
