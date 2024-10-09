from datetime import datetime
from enum import Enum

import numpy as np

from ell.types.message import Field, Message

from sqlmodel import Column, Field, SQLModel, Relationship, JSON
from typing import Dict, List, Literal, Union, Any, Optional, cast

from pydantic import field_validator

from sqlalchemy import func


from .core import Invocation, SerializedLMP, UTCTimestampField

#############################1
### Evaluation & Labeling ###
#############################
class EvaluationLabelerType(str, Enum):
    METRIC = "metric"
    ANNOTATION = "annotation"
    CRITERION = "criterion"

class EvaluationLabeler(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: EvaluationLabelerType

    labeling_lmp_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id")
    evaluation_id : str = Field(default=None, foreign_key="evaluation.id")

    
    # unused for now
    labeling_rubric: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
      
    @field_validator("labeling_lmp_id", "labeling_rubric")
    def validate_labeler_or_instructions(cls, v, values):
        if "labeling_lmp_id" not in values and "labeling_rubric" not in values:
            raise ValueError("Either labeler_lmp_id or instructions must be set")
        return v
    
    evaluation : "Evaluation" = Relationship(back_populates="labelers")
    labeling_lmp : Optional["SerializedLMP"] = Relationship(back_populates="labelers")
    labels: List["EvaluationLabel"] = Relationship(back_populates="labeler")
    evaluation_run_summaries: List["EvaluationRunLabelerSummary"] = Relationship(back_populates="evaluation_labeler")

class EvaluationLabel(SQLModel, table=True):
    # one label per labled datappooint
    labeled_datapoint_id: str = Field(default=None, foreign_key="evaluationresultdatapoint.id", primary_key=True)
    labeler_id: str = Field(default=None, foreign_key="evaluationlabeler.id", primary_key=True)

    # label.
    label_invocation_id: Optional[str] = Field(default=None, foreign_key="invocation.id")
    manual_label: Optional[Union[Dict[str, Any]]] = Field(
            default=None, sa_column=Column(JSON)
        ) # unused for now.
    
    # the invocaiton that was labeled.
    labeled_datapoint: "EvaluationResultDatapoint" = Relationship(back_populates="labels")
    labeler: "EvaluationLabeler" = Relationship(back_populates="labels")
    # the label itself.
    label_invocation: Optional[Invocation] = Relationship(back_populates="evaluation_labels")

class EvaluationResultDatapoint(SQLModel, table=True):
    # input  cannot produce two resutls per run & invocation id.
    invocation_being_labeled_id: str = Field(default=None, foreign_key="invocation.id", primary_key=True)
    evaluation_run_id: str = Field(foreign_key="evaluationrun.id", primary_key=True)

    invocation_being_labeled: Invocation = Relationship(back_populates="evaluation_result_datapoints")
    evaluation_run : "EvaluationRun" = Relationship(back_populates="results")
    labels: List[EvaluationLabel] = Relationship(back_populates="labeled_datapoint") # optional
    

# per labeler result aggregate should not be mutated, could be defiend as a true base to be reused within the use facing eval setup.
# XXX: Rename this at some point
class EvaluationRunLabelerSummary(SQLModel, table=True):
    evaluation_run_id: str = Field(default=None, foreign_key="evaluationrun.id", primary_key=True)
    evaluation_labeler_id: str = Field(default=None, foreign_key="evaluationlabeler.id", primary_key=True)

    created_at: datetime = UTCTimestampField(default=func.now())
    updated_at: Optional[datetime] = UTCTimestampField(default=None)
    finalized_at: Optional[datetime] = UTCTimestampField(default=None)

    is_scalar: bool = Field(default=False)
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    count: int = Field(default=0)

    evaluation_run: "EvaluationRun" = Relationship(back_populates="labeler_summaries")
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
        **other_keys: Dict[str, Any],
    ) -> "EvaluationRunLabelerSummary":
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


class EvaluationRun(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    evaluation_id: int = Field(foreign_key="evaluation.id")
    evaluated_lmp_id: str = Field(foreign_key="serializedlmp.lmp_id")
    api_params: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # we neeed to compute aggregatr statistics over the individual labels as a part of this run
    # Because of human labels these aggregates are now no longer considered finished until the end time and must be mutated by ell studio

    start_time: datetime = UTCTimestampField(default=None)
    end_time: Optional[datetime] = UTCTimestampField(default=None)

    # errors and success handling.
    success: bool = Field(default=False)
    error: Optional[str] = Field(default=None)
    
    evaluation: "Evaluation" = Relationship(back_populates="runs")
    evaluated_lmp: "SerializedLMP" = Relationship(back_populates="evaluation_runs")
    
    results: List[EvaluationResultDatapoint] = Relationship(back_populates="evaluation_run")
    labeler_summaries: List["EvaluationRunLabelerSummary"] = Relationship(back_populates="evaluation_run")


class Evaluation(SQLModel, table=True):
    name : str
    dataset_hash :  str # The idea here is we have the same input dataset we will re run over and over gain.
    n_evals : int 

    version_number: int = Field(default=0)
    commit_message: Optional[str] = Field(default=None)

    labelers: List["EvaluationLabeler"] = Relationship(back_populates="evaluation")
    runs: List["EvaluationRun"] = Relationship(back_populates="evaluation")


# Last thing we need is like run group so that the invocations dont all show up in the ui without groupings..
# class RunGroup(SQLModel, table=True):
#     id: Optional[str] = Field(default=None, primary_key=True)
#     name: str
#     parent_id: Optional[str] = Field(default=None, foreign_key="rungroup.id")
    
#     # Relationships
#     parent: Optional["RunGroup"] = Relationship(back_populates="children", sa_relationship_kwargs={"remote_side": [id]})
#     children: List["RunGroup"] = Relationship(back_populates="parent")

#     # Optional additional fields
#     description: Optional[str] = Field(default=None)
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_at: datetime = Field(default_factory=datetime.utcnow)


# TODO: FUTURE GENERALOIZATION OF EVALUATION RESULTS

# class _DatapointDatasetLink(SQLModel, table=True):
#     label_datapoint_id: str = Field(default=None, foreign_key="labeldatapoint.id", primary_key=True)
#     dataset_id: str = Field(default=None, foreign_key="multilabeldataset.id", primary_key=True)


# class EvaluationResultDataset(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     datapoints : List[EvaluationResultDatapoint] = Relationship(back_populates="dataset", link_model=_DatapointDatasetLink)
    
#     # Now this is redudnatn
#     # two joins through evaluation
#     evaluation_run_id: str = Field(default=None, foreign_key="evaluationrun.id")
#     evaluation_run : "EvaluationRun" = Relationship(back_populates="results")

# In the future use the geneirc datapoitn dataset link.
# This migration will be so messy.
# XXX: We jsut need to make really good migrations.