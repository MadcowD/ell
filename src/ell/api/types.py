from typing import Annotated, Any, Dict,  Optional, cast
from datetime import datetime, timezone

from openai import BaseModel
from pydantic import AwareDatetime, BeforeValidator, Field

from ell.types import SerializedLMP, utc_now


def iso_timestamp_to_utc_datetime(v: datetime) -> datetime:
    if isinstance(v, str):
        return datetime.fromisoformat(v).replace(tzinfo=timezone.utc)
    # elif isinstance(v, datetime):
    #     if v.tzinfo is not timezone.utc:
    #         raise ValueError(f"Invalid value for UTCTimestampField: {v}")
    #     return v
    elif v is None:
        return None
    raise ValueError(f"Invalid value for UTCTimestampField: {v}")


# todo. does pydantic compose optional with this or do we have to in the before validator...?
UTCTimestamp = Annotated[AwareDatetime,
                         BeforeValidator(iso_timestamp_to_utc_datetime)]


class WriteLMPInput(BaseModel):
    """
    Arguments to write a LMP.
    """
    lmp_id: str
    name: str
    source: str
    dependencies: str
    is_lm: bool
    lm_kwargs: Optional[Dict[str, Any]]
    initial_free_vars: Optional[Dict[str, Any]]
    initial_global_vars: Optional[Dict[str, Any]]
    # num_invocations: Optional[int]
    commit_message: Optional[str]
    version_number: Optional[int]
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

GetLMPResponse = LMP
# class LMPCreatedEvent(BaseModel):
#     lmp: LMP
#     uses: List[str]
