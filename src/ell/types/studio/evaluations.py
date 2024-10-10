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

class EvaluationLabeler(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True) # labeler-evaluation-id-name-type

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
        

    @lru_cache(maxsize=128)
    @staticmethod
    def generate_id(evaluation_id: str, name: str, type: EvaluationLabelerType) -> str:
        
        return f"labeler-{evaluation_id}-{name}-{type.name}"
    
    name: str
    type: EvaluationLabelerType

    labeling_lmp_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", index=True)
    evaluation_id : str = Field(default=None, foreign_key="serializedevaluation.id")

    
    # unused for now
    labeling_rubric: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
      
    @field_validator("labeling_lmp_id", "labeling_rubric")
    def validate_labeler_or_instructions(cls, v, values):
        if "labeling_lmp_id" not in values and "labeling_rubric" not in values:
            raise ValueError("Either labeler_lmp_id or instructions must be set")
        return v
    
    evaluation : "SerializedEvaluation" = Relationship(back_populates="labelers")
    labeling_lmp : Optional["SerializedLMP"] = Relationship() # TODO: Add backpopulate if needed
    labels: List["EvaluationLabel"] = Relationship(back_populates="labeler")
    evaluation_run_summaries: List["EvaluationRunLabelerSummary"] = Relationship(back_populates="evaluation_labeler")


class EvaluationLabel(SQLModel, table=True):
    # Composite foreign keys referencing the primary key of EvaluationResultDatapoint
    # BECAUSE WE ALWAYS LABEL AN INVOCATION.
    labeled_datapoint_id : int = Field(
        foreign_key="evaluationresultdatapoint.id",
        primary_key=True
    )
    labeler_id: str = Field(
        foreign_key="evaluationlabeler.id",
        primary_key=True
    )

    # Label fields
    label_invocation_id: Optional[str] = Field(default=None, foreign_key="invocation.id")
    manual_label: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )

    labeled_datapoint: "EvaluationResultDatapoint" = Relationship(back_populates="labels")
    labeler: "EvaluationLabeler" = Relationship(back_populates="labels")
    label_invocation: Optional[Invocation] = Relationship() # Add back popualte if you need to see how & if an invocation was used as a label.

class EvaluationResultDatapoint(SQLModel, table=True):
    # or this could just have an id. Feels pretty redudnant to have htis group table if the ids of evaluation label are the invocation being labeled & the run id
    # input  cannot produce two resutls per run & invocation id.
    id: Optional[int] = Field(default=None, primary_key=True)
    invocation_being_labeled_id: str = Field(foreign_key="invocation.id")
    evaluation_run_id: str = Field(foreign_key="serializedevaluationrun.id")

    invocation_being_labeled: Invocation = Relationship(back_populates="evaluation_result_datapoints")
    evaluation_run : "SerializedEvaluationRun" = Relationship(back_populates="results")
    labels: List[EvaluationLabel] = Relationship(back_populates="labeled_datapoint") # optional
    

# per labeler result aggregate should not be mutated, could be defiend as a true base to be reused within the use facing eval setup.
# XXX: Rename this at some point
class EvaluationRunLabelerSummary(SQLModel, table=True):
    evaluation_run_id: int = Field(foreign_key="serializedevaluationrun.id", primary_key=True)
    evaluation_labeler_id: str = Field(foreign_key="evaluationlabeler.id", primary_key=True)

    created_at: datetime = UTCTimestampField(default=func.now())
    updated_at: Optional[datetime] = UTCTimestampField(default=None)
    finalized_at: Optional[datetime] = UTCTimestampField(default=None)

    is_scalar: bool = Field(default=False)
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    count: int = Field(default=0)

    evaluation_run: "SerializedEvaluationRun" = Relationship(back_populates="labeler_summaries")
    evaluation_labeler: "EvaluationLabeler" = Relationship(back_populates="evaluation_run_summaries")

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


class SerializedEvaluationRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    evaluation_id: int = Field(foreign_key="serializedevaluation.id", index=True)
    evaluated_lmp_id: str = Field(foreign_key="serializedlmp.lmp_id", index=True)
    api_params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # we neeed to compute aggregatr statistics over the individual labels as a part of this run
    # Because of human labels these aggregates are now no longer considered finished until the end time and must be mutated by ell studio

    start_time: datetime = UTCTimestampField()
    end_time: Optional[datetime] = UTCTimestampField(default=None)

    # errors and success handling.
    success: bool 
    error: Optional[str] = Field(default=None)
    
    evaluation: "SerializedEvaluation" = Relationship(back_populates="runs")
    evaluated_lmp: "SerializedLMP" = Relationship(back_populates="evaluation_runs")
    
    results: List[EvaluationResultDatapoint] = Relationship(back_populates="evaluation_run")
    labeler_summaries: List["EvaluationRunLabelerSummary"] = Relationship(back_populates="evaluation_run")


class SerializedEvaluation(SQLModel, table=True):
    id : str = Field(primary_key=True) # the hash of the input dataset hash + the lmp hashes of all of the labelers 
    @field_validator("id")
    def validate_id(cls, v):
        if v is not None:
            assert v.startswith("evaluation-")
            assert v.count("-") == 1
            return v
        return v
    
    name : str
    dataset_hash : str # The idea here is we have the same input dataset we will re run over and over gain.
    n_evals : int 

    version_number: int = Field(default=0)
    commit_message: Optional[str] = Field(default=None)

    labelers: List["EvaluationLabeler"] = Relationship(back_populates="evaluation")
    runs: List["SerializedEvaluationRun"] = Relationship(back_populates="evaluation")

    def get_labeler(self, type: EvaluationLabelerType, name: Optional[str] = None) -> Optional[EvaluationLabeler]:
        """
        Get a labeler by type and optionally by name.

        Args:
            type (EvaluationLabelerType): The type of the labeler.
            name (Optional[str], optional): The name of the labeler. Defaults to None.

        Returns:
            Optional[EvaluationLabeler]: The matching labeler, or None if not found.
        """
        for labeler in self.labelers:
            if labeler.type == type and (name is None or labeler.name == name):
                return labeler
        return None
