from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, Generic
from pydantic import BaseModel, ConfigDict, Field
import numpy as np
from dataclasses import dataclass

Datapoint = Dict[str, Any]
Dataset = List[Dict[str, Any]]
Metric = Callable[[Datapoint, Any], float]
Metrics = Dict[str, Metric]
Criterion = Callable[[Datapoint, Any], bool]
Annotation = Callable[[Datapoint, Any], Any]
Annotations = Dict[str, Annotation]
InvocationID = str


# scores now doesn't make sense fulyl because of some other factors.
# We can ignore human feedback for now even though it's the most interesting.
@dataclass
class _ResultDatapoint:
    output: Any
    metrics: Dict[str, Tuple[float, InvocationID]]
    annotations: Dict[str, Tuple[Any, InvocationID]]
    criterion: Optional[Tuple[bool, InvocationID]]
    # XXX: EvaluationResutlDatapoitns should be written during the run I think.

T = TypeVar("T")
class EvaluationResults(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    outputs: Union[List[Any], List[T]] = Field(default_factory=list)
    metrics: Dict[str, Union[List[float], np.ndarray[float], List[T]]] = Field(
        default_factory=dict
    )
    annotations: Dict[str, Union[List[Any], List[T]]] = Field(default_factory=dict)
    criterion: Optional[Union[List[bool], np.ndarray[bool], List[T]]] = Field(
        default=None
    )

    invocation_ids: Optional["EvaluationResults[InvocationID]"] = Field(default=None)

    @staticmethod
    def from_rowar_results(
        rowar_results: List[_ResultDatapoint],
    ) -> "EvaluationResults":
        return EvaluationResults[None](
            outputs=[result.output[0] for result in rowar_results],
            metrics={
                name: np.array([result.metrics[name][0] for result in rowar_results])
                for name in rowar_results[0].metrics
            },
            annotations={
                name: ([result.annotations[name][0] for result in rowar_results])
                for name in rowar_results[0].annotations
            },
            criterion=(
                [
                    cast(Tuple[bool, InvocationID], result.criterion)[0]
                    for result in rowar_results
                ]
                if rowar_results[0].criterion
                else None
            ),
            invocation_ids=EvaluationResults[str](
                outputs=[result.output[1] for result in rowar_results],
                metrics={
                    name: np.array(
                        [result.metrics[name][1] for result in rowar_results]
                    )
                    for name in rowar_results[0].metrics
                },
                annotations={
                    name: ([result.annotations[name][1] for result in rowar_results])
                    for name in rowar_results[0].annotations
                },
                criterion=(
                    [
                        cast(Tuple[bool, InvocationID], result.criterion)[1]
                        for result in rowar_results
                    ]
                    if rowar_results[0].criterion
                    else None
                ),
            ),
        )
