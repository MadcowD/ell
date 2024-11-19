from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, Generic, cast
from pydantic import BaseModel, ConfigDict, Field
import numpy as np
from dataclasses import dataclass, field

from ell.stores.models.evaluations import EvaluationLabelerType

Datapoint = Dict[str, Any]
Dataset = List[Dict[str, Any]]
Metric = Callable[[Datapoint, Any], float]
Metrics = Dict[str, Metric]
Criterion = Callable[[Datapoint, Any], bool]
Annotation = Callable[[Datapoint, Any], Any]
Annotations = Dict[str, Annotation]
InvocationID = str

G = TypeVar("G")
@dataclass
class LabelGeneric(Generic[G]):
    name: str
    type: EvaluationLabelerType
    label: G

Labeler = LabelGeneric[Callable[[Any, Any], Union[Any, Tuple[Any, InvocationID]]]]
Label = LabelGeneric[Tuple[Any, InvocationID]]

class LabelListMixin:
    def __post_init__(self):
        # Make sure that labels is in the dataclass fields
        if "labels" not in self.__dataclass_fields__:
            raise ValueError("Labels must be in the dataclass fields")
        self.labels = cast(List[Label], self.labels)
    @property
    def metrics(self):
        return {l.name: l.label for l in self.labels if l.type == EvaluationLabelerType.METRIC}
    @property
    def annotations(self):
        return {l.name: l.label for l in self.labels if l.type == EvaluationLabelerType.ANNOTATION}
    @property
    def criterion(self):
        return next((l.label for l in self.labels if l.type == EvaluationLabelerType.CRITERION), None)


# scores now doesn't make sense fulyl because of some other factors.
# We can ignore human feedback for now even though it's the most interesting.
@dataclass
class _ResultDatapoint(LabelListMixin):
    output: Any
    labels: List[Label]

T = TypeVar("T")
@dataclass
class EvaluationResults(Generic[T], LabelListMixin):
    outputs: Union[List[Any], List[T]] = field(default_factory=list)
    labels: Union[LabelGeneric[np.ndarray[Any]], LabelGeneric[np.ndarray[T]]] = field(default_factory=list)
    invocation_ids: Optional["EvaluationResults[InvocationID]"] = field(default=None)

    @staticmethod
    def from_rowar_results(
        rowar_results: List[_ResultDatapoint],
    ) -> "EvaluationResults":
        def extract_labels(is_invocation: bool):
            if not rowar_results[0].labels:
                return []
            
            # Group labels by name and type
            label_groups: Dict[Tuple[str, EvaluationLabelerType], List[Any]] = {}
            for result in rowar_results:
                for label in result.labels:
                    key = (label.name, label.type)
                    if key not in label_groups:
                        label_groups[key] = []
                    label_groups[key].append(label.label[int(is_invocation)])
            
            # Create LabelGeneric objects with vertically stacked labels
            return [
                LabelGeneric(
                    name=name,
                    type=type_,
                    label=np.array(labels) # Everything is a numpy array.
                )
                for (name, type_), labels in label_groups.items()
            ]
        return EvaluationResults[None](
            outputs=[result.output[0] for result in rowar_results],
            labels=extract_labels(False),
            invocation_ids=EvaluationResults[str](
                outputs=[result.output[1] for result in rowar_results],
                labels=extract_labels(True)
            ),
        )