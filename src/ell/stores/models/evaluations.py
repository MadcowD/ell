from datetime import datetime
from enum import Enum
from functools import lru_cache

import numpy as np

from ell.types.message import Field, Message

from sqlmodel import Column, Field, SQLModel, Relationship, JSON
from typing import Dict, List, Literal, Union, Any, Optional, cast

from pydantic import field_validator

from sqlalchemy import func

from .core import Invocation, SerializedLMP, UTCTimestampField

#############################
### Evaluation & Labeling ###
#############################
class EvaluationLabelerType(str, Enum):
    METRIC = "metric"
    ANNOTATION = "annotation"
    CRITERION = "criterion"

class EvaluationLabelerBase(SQLModel):
    id: str = Field(primary_key=True)
    name: str
    type: EvaluationLabelerType
    labeling_lmp_id: Optional[str] = Field(
        default=None, foreign_key="serializedlmp.lmp_id", index=True
    )
    evaluation_id: str = Field(foreign_key="serializedevaluation.id")
    labeling_rubric: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )

class EvaluationLabeler(EvaluationLabelerBase, table=True):
    evaluation: "SerializedEvaluation" = Relationship(back_populates="labelers")
    labeling_lmp: Optional[SerializedLMP] = Relationship()
    labels: List["EvaluationLabel"] = Relationship(back_populates="labeler")
    evaluation_run_summaries: List["EvaluationRunLabelerSummary"] = Relationship(back_populates="evaluation_labeler")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = EvaluationLabeler.generate_id(self.evaluation_id, self.name, self.type)

    @field_validator("id")
    def validate_id(cls, v):
        if v is not None:
            assert v.startswith("labeler-")
            evaluation, eid, name, type = v.split("-")[1:]
            assert evaluation == "evaluation"
            assert type in EvaluationLabelerType.__members__
            return v

    @staticmethod
    @lru_cache(maxsize=128)
    def generate_id(evaluation_id: str, name: str, type: EvaluationLabelerType) -> str:
        return f"labeler-{evaluation_id}-{name}-{type.name}"

    @field_validator("labeling_lmp_id", "labeling_rubric")
    def validate_labeler_or_instructions(cls, v, values):
        if "labeling_lmp_id" not in values and "labeling_rubric" not in values:
            raise ValueError("Either labeler_lmp_id or instructions must be set")
        return v

class EvaluationLabelBase(SQLModel):

    labeler_id: str = Field(
        foreign_key="evaluationlabeler.id", 
        primary_key=True,
    )
    labeled_datapoint_id: int = Field(
        foreign_key="evaluationresultdatapoint.id", 
        primary_key=True,
    )
    label_invocation_id: Optional[str] = Field(
        default=None, foreign_key="invocation.id"
    )
    manual_label: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )

class EvaluationLabel(EvaluationLabelBase, table=True):
    labeled_datapoint: "EvaluationResultDatapoint" = Relationship(back_populates="labels")
    labeler: EvaluationLabeler = Relationship(back_populates="labels")
    label_invocation: Optional[Invocation] = Relationship()

class EvaluationResultDatapointBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    invocation_being_labeled_id: str = Field(
        foreign_key="invocation.id"
    )
    evaluation_run_id: int = Field(foreign_key="serializedevaluationrun.id")

class EvaluationResultDatapoint(EvaluationResultDatapointBase, table=True):
    invocation_being_labeled: Invocation = Relationship(back_populates="evaluation_result_datapoints")
    evaluation_run: "SerializedEvaluationRun" = Relationship(back_populates="results")
    labels: List[EvaluationLabel] = Relationship(back_populates="labeled_datapoint")

class EvaluationRunLabelerSummaryBase(SQLModel):
    evaluation_labeler_id: str = Field(foreign_key="evaluationlabeler.id", primary_key=True)
    evaluation_run_id: int = Field(foreign_key="serializedevaluationrun.id", primary_key=True)
    created_at: datetime = UTCTimestampField(default=func.now())
    updated_at: Optional[datetime] = UTCTimestampField(default=None)
    finalized_at: Optional[datetime] = UTCTimestampField(default=None)
    is_scalar: bool = Field(default=False)
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    count: int = Field(default=0)

class EvaluationRunLabelerSummary(EvaluationRunLabelerSummaryBase, table=True):
    evaluation_run: "SerializedEvaluationRun" = Relationship(back_populates="labeler_summaries")
    evaluation_labeler: EvaluationLabeler = Relationship(back_populates="evaluation_run_summaries")

    def mean(
        self,
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively("_mean")

    def std(
        self,
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively("_std")

    def min(
        self,
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively("_min")

    def max(
        self,
    ) -> Union[float, Dict[str, Any], List[Union[float, Dict[str, Any], None]], None]:
        return self._get_value_recursively("_max")

    @classmethod
    def from_labels(
        cls,
        data: Union[List[float], List[Dict[str, Any]]],
        **other_keys
    ) -> "EvaluationRunLabelerSummary":
        if len(data) == 0:
            # XXXL revisit.
            raise ValueError(
                "Aggregated run cannot contain empty data, at least one datapoint is required."
            )
    
        stats = lambda x: {
            "mean": float(np.mean(x)),
            "std": float(np.std(x)),
            "min": float(np.min(x)),
            "max": float(np.max(x)),
        }
        try:
            return cls(
                is_scalar=True,
                data=stats(data),
                count=len(data),
                **other_keys,
            )
        except TypeError:
            def recursive_aggregate(items):
                try:
                    if all(isinstance(item, dict) for item in items):
                        result = {}
                        for key in items[0].keys():
                            values = [item[key] for item in items if key in item]
                            result[key] = recursive_aggregate(values)
                        return result
                    else:
                        return stats(items)
                except TypeError:
                    return {
                        "mean": None,
                        "std": None,
                        "min": None,
                        "max": None,
                    }

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

class SerializedEvaluationRunBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    evaluation_id: str = Field(
        foreign_key="serializedevaluation.id", index=True
    )
    evaluated_lmp_id: str = Field(
        foreign_key="serializedlmp.lmp_id", index=True
    )
    api_params: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
    start_time: datetime = UTCTimestampField()
    end_time: Optional[datetime] = UTCTimestampField(default=None)
    success: Optional[bool] = Field(default=None)
    error: Optional[str] = Field(default=None)

class SerializedEvaluationRun(SerializedEvaluationRunBase, table=True):
    evaluated_lmp: SerializedLMP = Relationship(back_populates="evaluation_runs")
    evaluation: "SerializedEvaluation" = Relationship(back_populates="runs")
    results: List[EvaluationResultDatapoint] = Relationship(back_populates="evaluation_run")
    labeler_summaries: List[EvaluationRunLabelerSummary] = Relationship(back_populates="evaluation_run")

class SerializedEvaluationBase(SQLModel):
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime = UTCTimestampField(default=func.now(), nullable=False)
    dataset_id: str
    n_evals: int
    version_number: int = Field(default=0)
    commit_message: Optional[str] = Field(default=None)

class SerializedEvaluation(SerializedEvaluationBase, table=True):
    labelers: List[EvaluationLabeler] = Relationship(back_populates="evaluation")
    runs: List[SerializedEvaluationRun] = Relationship(back_populates="evaluation")

    @field_validator("id")
    def validate_id(cls, v):
        if v is not None:
            assert v.startswith("evaluation-")
            assert v.count("-") == 1
            return v
        return v

    def get_labeler(self, type: EvaluationLabelerType, name: Optional[str] = None) -> Optional[EvaluationLabeler]:
        for labeler in self.labelers:
            if labeler.type == type and (name is None or labeler.name == name):
                return labeler
        return None