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


from .core import Invocation, SerializedLMP, UTCTimestampField

#############################
### Evaluation & Labeling ###
#############################


class InvocationLabel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    labeler_id: str = Field(default=None, foreign_key="invocationlabeler.id")
    labeled_invocation_id: str = Field(foreign_key="invocation.id")
    # LABEL
    lmp_label_invocation_id: Optional[str] = Field(
        default=None, foreign_key="invocation.id"
    )
    # XXX: Human labeling and HP's in general should exist in a better schema eventually this would be the invocaiton contents of a human LMP which migth actually use an invocation as its core data type with an aggregate LMP | HFP as the generator of the invocation.
    manual_label: Optional[Union[Dict[str, Any]]] = Field(
        default=None, sa_column=Column(JSON)
    )
    deferred: bool = Field(default=False)  # for now = False

    labeler: "InvocationLabeler" = Relationship(back_populates="labels")
    labeled_invocation: Invocation = Relationship(
        back_populates="labels",
        sa_relationship_kwargs={"primaryjoin": "InvocationLabel.labeled_invocation_id == Invocation.id"},
    )
    lmp_label_invocation: Optional[Invocation] = Relationship(
        back_populates="lmp_labels",
        sa_relationship_kwargs={"primaryjoin": "InvocationLabel.lmp_label_invocation_id == Invocation.id"},
    )


class InvocationLabeler(SQLModel, table=True):
    # many to many link between evaluation and labelers
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str

    # Automaticalyl generated label via an LMP
    lmp_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id")

    # XXX: Move evaluation rubric to a new table in the future with lexical closure of generating pydantic schemas and proper linkage as with LMP we could call it HumanProgram or somethign.
    rubric_schema: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )

    evaluation_id: Optional[str] = Field(default=None, foreign_key="evaluation.id")

    
    @field_validator("lmp_id", "rubric_schema")
    def validate_labeler_or_instructions(cls, v, values):
        if "lmp_id" not in values and "rubric" not in values:
            raise ValueError("Either labeler_lmp_id or instructions must be set")
        return v

    labels: List["InvocationLabel"] = Relationship(back_populates="labeler")
    lmp: Optional["SerializedLMP"] = Relationship(back_populates="labelers")
    evaluation: Optional["Evaluation"] = Relationship(back_populates="labelers")


# per labeler result aggregate
class EvaluationRunLabelerResult(SQLModel, table=True):
    created_at: datetime = UTCTimestampField(default=func.now())
    updated_at: datetime = UTCTimestampField(default=func.now())
    finalized_at: datetime = UTCTimestampField(default=None)  # We have to
    evaluation_run_id: str = Field(default=None, foreign_key="evaluationrun.id", primary_key=True)
    invocation_labeler_id: str = Field(default=None, foreign_key="invocationlabeler.id", primary_key=True)

    is_scalar: bool = Field(default=False)
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    count: int = Field(default=0)

    evaluation_run: "EvaluationRun" = Relationship(back_populates="results")
    invocation_labeler: "InvocationLabeler" = Relationship(back_populates="results")

    @property
    def mean(
        self,
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively("_mean")

    @property
    def std(
        self,
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively("_std")

    @property
    def min(
        self,
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively("_min")

    @property
    def max(
        self,
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively("_max")

    @classmethod
    def from_labels(
        cls,
        data: Union[List[float], List[Dict[str, Any]]],
        **other_keys: Dict[str, Any],
    ) -> "EvaluationRunLabelerResult":
        if len(data) == 0:
            # XXXL revisit.
            raise ValueError(
                "Aggregated run cannot contain empty data, at least one datapoint is required."
            )

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
                    "max": max_value,
                },
                count=len(scalar_data),
                **other_keys,
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
                        "max": max(items),
                    }
                else:
                    return None

            aggregated_data = recursive_aggregate(data)

            return cls(
                is_scalar=False, data=aggregated_data, count=len(data), **other_keys
            )

    def _get_value_recursively(
        self, key: str, value=None
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
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
                    return {
                        k: self._get_value_recursively(key, v) for k, v in value.items()
                    }
            else:
                raise RuntimeError(
                    f"Failed to acceses {key} of the aggregated evaluation run result. The object schema does not conform to the expected schema. Current object: {self.data}"
                )

    def update(self, new_data: Union[float, Dict[str, Any]]):
        raise NotImplementedError(
            "Ell studio does not currently support updating evaluation run results with new data."
        )


# THis is a form of dataset that we should probably move to a more general form.


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
    success: bool = Field(default=False)
    error: Optional[str] = Field(default=None)

    evaluation: "Evaluation" = Relationship(back_populates="runs")
    evaluated_lmp: "SerializedLMP" = Relationship(back_populates="evaluation_runs")
    results: List[EvaluationRunLabelerResult] = Relationship(back_populates="evaluation_run")


class Evaluation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # no ability for us to reconstitue the dataset from the store for now
    dataset_hash: Optional[str] = Field(default=None)
    n_evals: Optional[int] = Field(default=None)

    @field_validator("dataset_hash", "n_evals")
    def validate_dataset_or_n_evals(cls, v, values):
        if "dataset_hash" not in values and "n_evals" not in values:
            raise ValueError("Either dataset_hash or n_evals must be specified")
        return v
    
    runs: List[EvaluationRun] = Relationship(back_populates="evaluation")
    labelers: List[InvocationLabeler] = Relationship(back_populates="evaluation")
    