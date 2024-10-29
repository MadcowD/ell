from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, Generic, cast
from pydantic import BaseModel, ConfigDict, Field
import numpy as np
from dataclasses import dataclass, field

from ell.types.studio.evaluations import EvaluationLabelerType

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


# scores now doesn't make sense fulyl because of some other factors.
# We can ignore human feedback for now even though it's the most interesting.
@dataclass
class _ResultDatapoint:
    output: Any
    labels: List[Label]

    @property
    def metrics(self) -> Dict[str, Tuple[float, InvocationID]]:
        return {l.name: (l.label[0], l.label[1]) for l in self.labels if l.type == EvaluationLabelerType.METRIC}
    @property
    def annotations(self) -> Dict[str, Tuple[Any, InvocationID]]:
        return {l.name: (l.label[0], l.label[1]) for l in self.labels if l.type == EvaluationLabelerType.ANNOTATION}
    @property
    def criterion(self) -> Optional[Tuple[bool, InvocationID]]:
        return next((l.label for l in self.labels if l.type == EvaluationLabelerType.CRITERION), None)

T = TypeVar("T")
@dataclass
class EvaluationResults(Generic[T]):
    outputs: Union[List[Any], List[T]] = field(default_factory=list)
    labels: List[Union[LabelGeneric[Any], LabelGeneric[T]]] = field(default_factory=list)
    invocation_ids: Optional["EvaluationResults[InvocationID]"] = field(default=None)

    @staticmethod
    def from_rowar_results(
        rowar_results: List[_ResultDatapoint],
    ) -> "EvaluationResults":
    
        def extract_labels(is_invocation: bool):
            if not rowar_results[0].labels:
                return []
            return [
                LabelGeneric(
                    name=label.name,
                    type=label.type,
                    label=label.label[int(is_invocation)]
                )
                for result in rowar_results
                for label in result.labels
            ]
        return EvaluationResults[None](
            outputs=[result.output[0] for result in rowar_results],
            labels=extract_labels(False),
            invocation_ids=EvaluationResults[str](
                outputs=[result.output[1] for result in rowar_results],
                labels=extract_labels(True)
            ),
        )

    @property
    def metrics(self):
        return {l.name: l.label for l in self.labels if l.type == EvaluationLabelerType.METRIC}
    @property
    def annotations(self):
        return {l.name: l.label for l in self.labels if l.type == EvaluationLabelerType.ANNOTATION}
    @property
    def criterion(self):
        return next((l.label for l in self.labels if l.type == EvaluationLabelerType.CRITERION), None)
