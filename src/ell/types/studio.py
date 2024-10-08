from datetime import datetime, timezone
import enum
from functools import cached_property
from math import sqrt
from types import NoneType

import numpy as np
import sqlalchemy.types as types

from ell.types.message import Any, Any, Field, Message, Optional

from sqlmodel import Column, Field, SQLModel
from typing import Optional, cast
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
    METRIC = "METRIC"
    FUNCTION = "FUNCTION"
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


class ExternalizeableModel(SQLModel):
    is_external : bool = Field(default=False)


class InvocationContentsBase(ExternalizeableModel):
    invocation_id: str = Field(foreign_key="invocation.id", index=True, primary_key=True)
    params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    results: Optional[Union[List[Message], Any]] = Field(default=None, sa_column=Column(JSON))
    invocation_api_params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    global_vars: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    free_vars: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


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
            len(json.dumps(field, default=(lambda x: json.dumps(x.model_dump(), default=str) if isinstance(x, BaseModel) else str(x))).encode('utf-8')) for field in json_fields if field is not None
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


#############################
### Evaluation & Labeling ###
#############################

class InvocationLabel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    labeler_id : str = Field(default=None, foreign_key="invocationlabeler.id")
    

    labeled_invocation_id: str = Field(foreign_key="invocation.id")

    # LABEL
    lmp_label_invocation_id: Optional[str] = Field(default=None, foreign_key="invocation.id")
    # XXX: Human labeling and HP's in general should exist in a better schema eventually this would be the invocaiton contents of a human LMP which migth actually use an invocation as its core data type with an aggregate LMP | HFP as the generator of the invocation.
    human_label: Optional[Union[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    deferred: bool = Field(default=False) # for now = False

class InvocationLabeler(SQLModel, table=True):
    # many to many link between evaluation and labelers
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str

    # Automaticalyl generated label via an LMP
    lmp_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id")
    
    # XXX: Move evaluation rubric to a new table in the future with lexical closure of generating pydantic schemas and proper linkage as with LMP we could call it HumanProgram or somethign.
    human_rubric_schema : Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    evaluation_id: Optional[str] = Field(default=None, foreign_key="evaluation.id")

    @field_validator('lmp_id', 'rubric')
    def validate_labeler_or_instructions(cls, v, values):
        if 'lmp_id' not in values and 'rubric' not in values:
            raise ValueError("Either labeler_lmp_id or instructions must be set")
        return v

class EvaluationRunResult(SQLModel, table=True):
    created_at : datetime = UTCTimestampField(default=func.now())
    updated_at : datetime = UTCTimestampField(default=func.now())
    finalized_at : datetime = UTCTimestampField(default=None) # We have to 
    evaluation_run_id : str = Field(default=None, foreign_key="evaluationrun.id")
    invocation_labeler_id : str = Field(default=None, foreign_key="invocationlabeler.id")

    is_scalar : bool = Field(default=False)
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    count: int = Field(default=0)

    

    @property
    def mean(self) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively('_mean')

    @property
    def std(self) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively('_std')

    @property
    def min(self) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively('_min')

    @property
    def max(self) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively('_max')
    
    @classmethod
    def from_labels(cls,  data: Union[List[float], List[Dict[str, Any]]], **other_keys : Dict[str, Any]) -> "EvaluationRunResult":
        if len(data) == 0:
            # XXXL revisit.
            raise ValueError("Aggregated run cannot contain empty data, at least one datapoint is required.")
    
        is_scalar = all(isinstance(item, (int, float)) for item in data)
        
        if is_scalar:
            scalar_data = cast(List[float], data)
            mean_value = np.mean(scalar_data)
            std_value = np.std(scalar_data)
            min_value = min(scalar_data)
            max_value = max(scalar_data)
            
            return cls(
                is_scalar=True,
                data={
                    "mean": mean_value,
                    "std": std_value,
                    "min": min_value,
                    "max": max_value
                },
                count=len(scalar_data),
                **other_keys
            )
        else:
            def recursive_aggregate(items):
                if all(isinstance(item, dict) for item in items):
                    result = {}
                    for key in items[0].keys():
                        values = [item[key] for item in items if key in item]
                        result[key] = recursive_aggregate(values)
                    return result
                elif all(isinstance(item, (int, float)) for item in items):
                    return {
                        "mean": np.mean(items),
                        "std": np.std(items),
                        "min": min(items),
                        "max": max(items)
                    }
                else:
                    return None
            
            aggregated_data = recursive_aggregate(data)
            
            return cls(
                is_scalar=False,
                data=aggregated_data,
                count=len(data),
                **other_keys
            )


    def _get_value_recursively(self, key: str, value = None) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        # recursively gets the value within the internal data structure
        if self.is_scalar:
            return self.data[key]
        else:
            # return the same schema of object as from which it was created but with the mean std min and max on each of the nested objects.
            if value is None:
                return None
            if isinstance(value, dict):
                # if _mean is in the dict.
                if (possible_result := value.get(key)) is not None:
                    return possible_result
                else:
                    return {k : self._get_value_recursively(key, v) for k, v in value.items()}
            else:
                raise RuntimeError(f"Failed to acceses {key} of the aggregated evaluation run result. The object schema does not conform to the expected schema. Current object: {self.data}")
            

    def update(self, new_data : Union[float, Dict[str, Any]]):
        raise NotImplementedError("Ell studio does not currently support updating evaluation run results with new data.")
        

class EvaluationRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    evaluation_id: int = Field(foreign_key="evaluation.id")
    evaluated_lmp_id: str = Field(foreign_key="serializedlmp.lmp_id")
    api_params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # we neeed to compute aggregatr statistics over the individual labels as a part of this run
    # Because of human labels these aggregates are now no longer considered finished until the end time and must be mutated by ell studio

    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # errors and success handling.
    success : bool = Field(default=False)
    error : Optional[str] = Field(default=None)


class Evaluation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # no ability for us to reconstitue the dataset from the store for now 
    dataset_hash : Optional[str] = Field(default=None)
    n_evals : Optional[int] = Field(default=None)

    @field_validator('dataset_hash', 'n_evals')
    def validate_dataset_or_n_evals(cls, v, values):
        if 'dataset_hash' not in values and 'n_evals' not in values:
            raise ValueError("Either dataset_hash or n_evals must be specified")
        return v
    # XXX: introduce option for multiplexing the evals.



########################
### Comparison
########################


# class Comparison(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     # independent of evaluation and actually needs a dataset object to specify the the evaluation criterion
#     # could also ahve hte same thing for human labels but we'll leave htis for now.
#     invocation_a_id : str = Field(foreign_key="invocation.id")
#     invocation_b_id : str = Field(foreign_key="invocation.id")
#     a_better_than_b : bool

