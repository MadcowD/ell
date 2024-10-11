from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import partial
import itertools
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union, cast
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

import openai

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlmodel._compat import SQLModelConfig
from ell.lmp._track import _track
from ell.types.message import LMP
import statistics
from ell.util.tqdm import tqdm
import contextlib
import dill
import hashlib


from ell.configurator import config

# from ell.types.studio import SerializedEvaluation
from ell.util.closure import lexical_closure, lexically_closured_source

from ell.types.studio.evaluations import (
    EvaluationLabel,
    SerializedEvaluation as SerializedEvaluation,
    EvaluationLabeler,
    EvaluationLabelerType,
    SerializedEvaluationRun,
    EvaluationResultDatapoint,
    EvaluationRunLabelerSummary
)

Datapoint = Dict[str, Any]
Dataset = List[Dict[str, Any]]
Metric = Callable[[Datapoint, Any], float]
Metrics = Dict[str, Metric]
Criterion = Callable[[Datapoint, Any], bool]
Annotation = Callable[[Datapoint, Any], Any]
Annotations = Dict[str, Annotation]
InvocationID = str

def ido(f): return f.__ell_func__.__ell_hash__
def hsh(x): return hashlib.md5(x.encode()).hexdigest()
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
    metrics: Dict[str, Union[List[float], np.ndarray[float], List[T]]] = Field(default_factory=dict)
    annotations: Dict[str, Union[List[Any], List[T]]] = Field(default_factory=dict)
    criterion: Optional[Union[List[bool], np.ndarray[bool], List[T]]] = Field(default=None)
    
    invocation_ids : Optional["EvaluationResults[InvocationID]"] = Field(default=None)

    @staticmethod
    def from_rowar_results(rowar_results: List[_ResultDatapoint]) -> "EvaluationResults":
        return  EvaluationResults[None](
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
                    [cast(Tuple[bool, InvocationID], result.criterion)[0] for result in rowar_results]
                    if rowar_results[0].criterion
                    else None
                ),
                invocation_ids = EvaluationResults[str](
                    outputs=[result.output[1] for result in rowar_results],
                    metrics={
                        name: np.array([result.metrics[name][1] for result in rowar_results])
                        for name in rowar_results[0].metrics
                    },
                    annotations={
                        name: ([result.annotations[name][1] for result in rowar_results])
                            for name in rowar_results[0].annotations
                            },
                    criterion=(
                        [cast(Tuple[bool, InvocationID], result.criterion)[1] for result in rowar_results]
                        if rowar_results[0].criterion
                        else None
                    ),
                )
            )



class EvaluationRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    results: EvaluationResults = Field(default_factory=EvaluationResults)
    dataset: Optional[Dataset] = Field(default=None)
    n_evals: Optional[int] = Field(default=None)
    samples_per_datapoint: int = Field(default=1)
    lmp: Optional[LMP] = Field(default=None)

    api_params: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def inputs(self) -> List[Any]:
        return [d["input"] for d in self.dataset] if self.dataset else []

    @property
    def outputs(self) -> List[Any]:
        return self.results.outputs
    
    @property
    def invocation_ids(self) -> Optional[EvaluationResults[InvocationID]]:
        return self.results.invocation_ids

    def _write(self, evaluation_id: str):
        if not config.store:
            return
        
        # Construct SerializedEvaluationRun
        serialized_run = SerializedEvaluationRun(
            evaluation_id=evaluation_id,
            evaluated_lmp_id=ido(self.lmp),
            api_params=self.api_params,
            start_time=self.start_time,
            end_time=self.end_time,
            success=True,  # Assuming the run was successful; you might want to add error handling
            error=None  # Add error information if needed
        )
        invocation_ids = self.results.invocation_ids
        # Create EvaluationResultDatapoints

        result_datapoints = []
        for i, output in enumerate(self.results.outputs):
            result_datapoint = EvaluationResultDatapoint(
                invocation_being_labeled_id=ido(self.lmp),
                evaluation_run_id=serialized_run.id,
                invocation_ids=invocation_ids.outputs[i]
            )

            for metric_name, metric_values in self.results.metrics.items():
                label = EvaluationLabel(
                    labeler_id=EvaluationLabeler.generate_id(evaluation_id=evaluation_id, name=metric_name, type=EvaluationLabelerType.METRIC),
                    label_invocation_id=invocation_ids.metrics[metric_name][i],
                )
                result_datapoint.labels.append(label)

            for annotation_name, annotation_values in self.results.annotations.items():
                label = EvaluationLabel(
                    labeled_datapoint_id=result_datapoint.id,
                    labeler_id=EvaluationLabeler.generate_id(evaluation_id=evaluation_id, name=annotation_name, type=EvaluationLabelerType.ANNOTATION),
                    label_invocation_id=invocation_ids.annotations[annotation_name][i],
                    
                )
                result_datapoint.labels.append(label)

            if self.results.criterion is not None:
                criterion_label = EvaluationLabel(
                    labeled_datapoint_id=result_datapoint.id,
                    labeler_id=EvaluationLabeler.generate_id(evaluation_id=evaluation_id, name="criterion", type=EvaluationLabelerType.CRITERION),
                    label_invocation_id=invocation_ids.criterion[i]
                )
                result_datapoint.labels.append(criterion_label)
            
        
            result_datapoints.append(result_datapoint)

        serialized_run.results = result_datapoints
        # Let;s add a result summary.

        id = config.store.write_evaluation_run(serialized_run)
        # write summaries now
        summaries = []
        for metric_name, metric_values in self.results.metrics.items():
            summaries.append(EvaluationRunLabelerSummary.from_labels(data=metric_values, evaluation_run_id=id, evaluation_labeler_id=EvaluationLabeler.generate_id(evaluation_id=evaluation_id, name=metric_name, type=EvaluationLabelerType.METRIC)))
        for annotation_name, annotation_values in self.results.annotations.items():
            summaries.append(EvaluationRunLabelerSummary.from_labels(data=annotation_values,  evaluation_run_id=id, evaluation_labeler_id=EvaluationLabeler.generate_id(evaluation_id=evaluation_id, name=annotation_name, type=EvaluationLabelerType.ANNOTATION)))
        if self.results.criterion is not None:
            summaries.append(EvaluationRunLabelerSummary.from_labels(data=self.results.criterion, evaluation_run_id=id, evaluation_labeler_id=EvaluationLabeler.generate_id(evaluation_id=evaluation_id, name="criterion", type=EvaluationLabelerType.CRITERION)))
        config.store.write_evaluation_run_labeler_summaries(summaries)

class Evaluation(BaseModel):
    """Simple evaluation for prompt engineering rigorously"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    dataset: Optional[Dataset] = Field(default=None)
    # XXX: Rename this for 0.1.0
    n_evals: Optional[int] = Field(
        default=None,
        description="If set, this will run the LMP n_evals times and evaluate the outputs. This is useful for LMPs without inputs where you want to evaluate metrics a number of times. ",
    )

    samples_per_datapoint: int = Field(
        default=1,
        description="How many samples per datapoint to generate, equivalent to setting n in api params for LMPs which support this When no dataset is provided then the total nubmer of evalautiosn will be samples_per_datapoint * n_evals..",
    )
    metrics: Metrics = Field(default_factory=dict)
    annotations: Annotations = Field(default_factory=dict)
    criterion: Optional[Criterion] = None

    default_api_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    serialized: Optional[SerializedEvaluation] = Field(default=None)

    id: Optional[str] = Field(default=None)

    def __init__(self, *args, **kwargs):
        assert (
            "dataset" in kwargs or "n_evals" in kwargs
        ), "Either dataset or n_evals must be set"
        assert not (
            "dataset" in kwargs and "n_evals" in kwargs
        ), "Either dataset or samples_per_datapoint must be set, not both"

        super().__init__(*args, **kwargs)

    @field_validator("metrics", "annotations", "criterion", mode="before")
    def wrap_callables_in_lmp_function(cls, value):
        from ell.lmp.function import function

        if isinstance(value, dict):
            return {
                k: (
                    function()(v)
                    if callable(v) and not hasattr(v, "__ell_track__")
                    else v
                )
                for k, v in value.items()
            }
        elif callable(value) and not hasattr(value, "__ell_track__"):
            return function()(value)
        elif value is None:
            return value
        else:
            raise ValueError(f"Expected dict, callable, or None, got {type(value)}")

    @field_validator("metrics")
    def validate_metrics(cls, metrics: Union[Metric, List[Metrics]]) -> Metric:
        return _validate_callable_dict(metrics, "metric")

    @field_validator("annotations")
    def validate_annotations(
        cls, annotations: Union[Annotations, List[Annotation]]
    ) -> Annotations:
        return _validate_callable_dict(annotations, "annotation")
    

    def write(self, evaluation_run: EvaluationRun) -> None:
        # Create a hash of the dataset and labelers
        if not config.store:
            return
        if not self.serialized:
            self.id = "evaluation-" + hsh(
                ((dataset_hash := hsh((str(dill.dumps(self.dataset)) if self.dataset else str(self.n_evals)) + str(self.samples_per_datapoint)))
                    + "".join(
                        sorted(metrics_ids := [ido(f) for f in self.metrics.values()])
                        + sorted(annotation_ids := [ido(a) for a in self.annotations.values()])
                        + (criteiron_ids := [ido(self.criterion)] if self.criterion else [])
                    )
                ))
            
            # get existing versions
            existing_versions = config.store.get_eval_versions_by_name(self.name)
            if any(v.id == self.id for v in existing_versions):
                self.serialized = existing_versions[0]
            else:
                version_number = max(itertools.chain(map( lambda x: x.version_number, existing_versions), [0])) + 1

                if config.autocommit:
                    # if not _autocommit_warning():
                    #     from ell.util.differ import write_commit_message_for_diff
                    #     self.serialized.commit_message = str(write_commit_message_for_diff(
                    #         f"{latest_version.dataset_hash}\n\n{latest_version.n_evals}",
                    #         f"{self.serialized.dataset_hash}\n\n{self.serialized.n_evals}"
                    #     )[0])
                    pass
                
                
                
                # Create SerializedEvaluation
                serialized_evaluation = SerializedEvaluation(
                    id=self.id,
                    name=self.name,
                    dataset_hash=dataset_hash,
                    n_evals=self.n_evals or len(self.dataset or []),
                    version_number=version_number,
                )

                # Create EvaluationLabelers
                labelers = []
                # Metrics
                for name, h in zip(self.metrics.keys(), metrics_ids):
                    labelers.append(
                        EvaluationLabeler(
                            name=name,
                            type=EvaluationLabelerType.METRIC,
                            evaluation_id=self.id,
                            labeling_lmp_id=h,
                        )
                    )

                # Annotations
                for name, h in zip(self.annotations.keys(), annotation_ids):
                    labelers.append(
                        EvaluationLabeler(
                            name=name,
                            type=EvaluationLabelerType.ANNOTATION,
                            evaluation_id=self.id,
                            labeling_lmp_id=h,
                        )
                    )

                # Criterion
                if self.criterion:
                    labelers.append(
                        EvaluationLabeler(
                            name="criterion",
                            type=EvaluationLabelerType.CRITERION,
                            evaluation_id=self.id,
                            labeling_lmp_id=criteiron_ids[0],
                        )
                    )

                # Add labelers to the serialized evaluation
                serialized_evaluation.labelers = labelers
                self.serialized = serialized_evaluation
                config.store.write_evaluation(serialized_evaluation)

        # Now serialize the evaluation run,
        evaluation_run._write(evaluation_id=self.id)

    # XXX: Dones't support partial params outside of the dataset like client??
    def run(
        self,
        lmp,
        *,
        n_workers: int = 1,
        use_api_batching: bool = False,
        api_params: Optional[Dict[str, Any]] = None,
        verbose: bool = False,
        **additional_lmp_params,
    ) -> EvaluationRun:
        """
        Run the evaluation or optimization using the specified number of workers.

        Args:
            n_workers (int): Number of parallel workers to use. Default is 1.
            lmp (Optional[LMP]): LMP to use for this run. If None, uses the LMP set during initialization.
            api_params (Dict[str, Any]): API parameters to override defaults.
            verbose (bool): Whether to run in verbose mode. Default is False.
            samples_per_datapoint (int): Number of samples to generate per datapoint. Default is 1.

        Returns:
            EvaluationRun: Object containing statistics about the evaluation or optimization outputs.
        """
        assert (
            "api_params" not in additional_lmp_params
        ), f"specify api_params directly to run not within additional_lmp_params: {additional_lmp_params}"
        # Inspect LMP signature to check for required arguments
        import inspect

        lmp_signature = inspect.signature(lmp)
        required_params = (
            len(
                {
                    param
                    for param in lmp_signature.parameters.values()
                    if param.default == param.empty and param.kind != param.VAR_KEYWORD
                }
            )
            > 0
        )

        run_api_params = {**(self.default_api_params or {}), **(api_params or {})}
        lmp_params = dict(api_params=run_api_params, **additional_lmp_params)

        dataset = self.dataset if self.dataset is not None else [{"input": None}]
        if use_api_batching:
            # we need to collate on unique datapoints here if possible; note that n_evals can never be set.
            run_api_params["n"] = self.samples_per_datapoint * (self.n_evals or 1)
        else:
            dataset = sum(
                [
                    [data_point] * self.samples_per_datapoint * (self.n_evals or 1)
                    for data_point in dataset
                ],
                [],
            )

        # we will try to run with n = samples_per_datapoint * n_evals first and if the api rejects n as a param then we need to do something will try the standard way with the thread pool executor.

        evaluation_run = EvaluationRun(
            lmp=lmp,
            dataset=self.dataset,
            n_evals=self.n_evals,
            samples_per_datapoint=self.samples_per_datapoint,
            api_params=run_api_params,
            start_time=datetime.now(),
        )
        original_verbose = config.verbose
        config.verbose = verbose
        try:
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                output_futures = [
                    executor.submit(
                        self._process_single,
                        data_point,
                        lmp,
                        lmp_params,
                        required_params,
                    )
                    for data_point in dataset
                ]
                metric_futures = []
                for future in tqdm(
                    as_completed(output_futures),
                    total=len(output_futures),
                    desc=f"{self.name} outputs",
                ):
                    get_outputs = future.result()
                    metric_futures.extend([executor.submit(o) for o in get_outputs])
                rowar_results = []
                for result_future in (
                    pbar := tqdm(
                        as_completed(metric_futures),
                        total=len(metric_futures),
                        desc=f"{self.name} results",
                    )
                ):
                    rowar_results.append(result_future.result())
                    pbar.set_description(
                        f"{self.name} (last={str(rowar_results[-1].output)[:10]})"
                    )

            evaluation_run.end_time = datetime.now()
            # convert rowar results to evaluation results
            evaluation_run.results = EvaluationResults.from_rowar_results(rowar_results)

            self.write(evaluation_run)

            return evaluation_run
        finally:
            config.verbose = original_verbose

    def _process_single(
        self,
        data_point: Datapoint,
        lmp: LMP,
        lmp_params: Dict[str, Any],
        required_params: bool,
    ) -> List[Any]:
        """
        Process a single data point using the LMP and apply all criteria.

        Args:
        data_point (Any): A single item from the dataset.
            lmp (LMP): The LMP to use for processing.
            api_params (Dict[str, Any]): API parameters for this run.

        Returns:
            Tuple[List[Any], Dict[str, List[float]]]: The LMP outputs and a dictionary of scores from all metrics.
        """
        lmp_params_with_invocation_id = {**lmp_params, "_get_invocation_id": True}
        lmp_output = (
                 lmp(**lmp_params_with_invocation_id) if not required_params  # type: ignore
            else (lmp(*inp, **lmp_params_with_invocation_id) if isinstance((inp := data_point["input"]), list)  # type: ignore
            else (lmp(**inp, **lmp_params_with_invocation_id) if isinstance(inp, dict)  # type: ignore
            else (_ for _ in ()).throw(ValueError(f"Invalid input type: {type(inp)}")))))

        if not isinstance(lmp_output, list):
            lmp_output = [cast(Any, lmp_output)]
        def process_rowar_results(output):
            return _ResultDatapoint(
                output=output,
                metrics={name: metric(data_point, output[0], _get_invocation_id=True) for name, metric in self.metrics.items()},
                annotations={name: annotation(data_point, output[0], _get_invocation_id=True) for name, annotation in self.annotations.items()},
                criterion=self.criterion(data_point, output[0], _get_invocation_id=True) if self.criterion else None,
            )
        return [partial(process_rowar_results, output) for output in lmp_output]


def _validate_callable_dict(
    items: Union[Dict[str, Callable], List[Callable]], item_type: str
) -> Dict[str, Callable]:
    if isinstance(items, list):
        items_dict = {}
        for item in items:
            if not callable(item):
                raise ValueError(
                    f"Each {item_type} must be a callable, got {type(item)}"
                )
            if not hasattr(item, "__name__") or item.__name__ == "<lambda>":
                raise ValueError(
                    f"Each {item_type} in a list must have a name (not a lambda)"
                )
            items_dict[item.__name__] = item
        return items_dict
    elif isinstance(items, dict):
        for name, item in items.items():
            if not callable(item):
                raise ValueError(
                    f"{item_type.capitalize()} '{name}' must be a callable, got {type(item)}"
                )
        return items
    else:
        raise ValueError(
            f"{item_type}s must be either a list of callables or a dictionary, got {type(items)}"
        )
