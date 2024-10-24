from datetime import datetime
from functools import partial
import itertools
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    cast,
)
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
from ell.evaluation.results import _ResultDatapoint, EvaluationResults
from ell.types.studio import LMPType
import openai
from ell.util.serialization import validate_callable_dict

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlmodel._compat import SQLModelConfig
from ell.lmp._track import _track
from ell.types.message import LMP
import statistics
from ell.util.closure_util import ido
from ell.util.closure_util import hsh
from ell.util.tqdm import tqdm
import dill


from ell.configurator import config

from ell.types.studio.evaluations import (
    EvaluationLabel,
    SerializedEvaluation as SerializedEvaluation,
    EvaluationLabeler,
    EvaluationLabelerType,
    SerializedEvaluationRun,
    EvaluationResultDatapoint,
    EvaluationRunLabelerSummary,
)

from ell.evaluation.results import *


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

    def write(self, evaluation_id: str):
        if not config.store:
            return

        # Construct SerializedEvaluationRun
        serialized_run = SerializedEvaluationRun(
            evaluation_id=evaluation_id,
            evaluated_lmp_id=ido(self.lmp),
            api_params=self.api_params,
            start_time=self.start_time,
            end_time=self.end_time,
            success=True,
            error=None,
        )
        invocation_ids = self.results.invocation_ids

        # Create EvaluationResultDatapoints
        result_datapoints = []
        for i, output in enumerate(self.results.outputs):
            result_datapoint = EvaluationResultDatapoint(
                invocation_being_labeled_id=ido(self.lmp),
                evaluation_run_id=serialized_run.id,
                invocation_ids=invocation_ids.outputs[i],
            )

            # Helper function to create labels
            def create_labels(values_dict, labeler_type, invocation_ids_dict):
                return [
                    EvaluationLabel(
                        labeled_datapoint_id=result_datapoint.id,
                        labeler_id=EvaluationLabeler.generate_id(
                            evaluation_id=evaluation_id, name=name, type=labeler_type
                        ),
                        label_invocation_id=invocation_ids_dict[name][i],
                    )
                    for name in values_dict
                ]

            # Create labels for metrics and annotations
            result_datapoint.labels.extend(create_labels(
                self.results.metrics, EvaluationLabelerType.METRIC, invocation_ids.metrics
            ))
            result_datapoint.labels.extend(create_labels(
                self.results.annotations, EvaluationLabelerType.ANNOTATION, invocation_ids.annotations
            ))

            # Create criterion labels if present
            if self.results.criterion is not None:
                result_datapoint.labels.extend(create_labels(
                    {"criterion": self.results.criterion},
                    EvaluationLabelerType.CRITERION,
                    {"criterion": invocation_ids.criterion}
                ))

            result_datapoints.append(result_datapoint)

        serialized_run.results = result_datapoints

        # Write summaries using a helper function
        def create_summaries(data_dict, labeler_type):
            return [
                EvaluationRunLabelerSummary.from_labels(
                    data=values,
                    evaluation_run_id=id,
                    evaluation_labeler_id=EvaluationLabeler.generate_id(
                        evaluation_id=evaluation_id,
                        name=name,
                        type=labeler_type,
                    ),
                )
                for name, values in data_dict.items()
            ]

        id = config.store.write_evaluation_run(serialized_run)

        # Collect summaries for metrics, annotations, and criterion
        summaries = create_summaries(self.results.metrics, EvaluationLabelerType.METRIC)
        summaries += create_summaries(self.results.annotations, EvaluationLabelerType.ANNOTATION)
        if self.results.criterion is not None:
            summaries += create_summaries({"criterion": self.results.criterion}, EvaluationLabelerType.CRITERION)

        config.store.write_evaluation_run_labeler_summaries(summaries)


class Evaluation(BaseModel):

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

    @model_validator(mode="before")
    @classmethod
    def validate_dataset_or_n_evals(cls, values):
        if "dataset" not in values and "n_evals" not in values:
            raise ValueError("Either dataset or n_evals must be set")
        if "dataset" in values and "n_evals" in values:
            raise ValueError("Either dataset or n_evals must be set, not both")
        return values

    @field_validator("metrics", "annotations", "criterion", mode="before")
    def wrap_callables_in_lmp_function(cls, value):
        from ell.lmp.function import function

        if isinstance(value, dict):
            return {
                k: (
                    function(type=LMPType.LABELR)(v)
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
        return validate_callable_dict(metrics, "metric")

    @field_validator("annotations")
    def validate_annotations(
        cls, annotations: Union[Annotations, List[Annotation]]
    ) -> Annotations:
        return validate_callable_dict(annotations, "annotation")

    def write(self, evaluation_run: EvaluationRun) -> None:
        # Create a hash of the dataset and labelers
        if not config.store:
            return
        if not self.serialized:
            dataset_hash = hsh(str(dill.dumps(self.dataset) if self.dataset else str(self.n_evals)) + str(self.samples_per_datapoint))
            metrics_ids = [ido(f) for f in self.metrics.values()]
            annotation_ids = [ido(a) for a in self.annotations.values()]
            criteiron_ids = [ido(self.criterion)] if self.criterion else []
            
            self.id = "evaluation-" + hsh(dataset_hash + "".join(sorted(metrics_ids) + sorted(annotation_ids) + criteiron_ids))

            # get existing versions
            existing_versions = config.store.get_eval_versions_by_name(self.name)
            if any(v.id == self.id for v in existing_versions):
                self.serialized = existing_versions[0]
            else:
                # TODO: Merge with other versioning code.
                version_number = (
                    max(
                        itertools.chain(
                            map(lambda x: x.version_number, existing_versions), [0]
                        )
                    )
                    + 1
                )

                if config.autocommit:
                    # TODO: Implement
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
                def create_labelers(names, ids, labeler_type):
                    return [
                        EvaluationLabeler(
                            name=name,
                            type=labeler_type,
                            evaluation_id=self.id,
                            labeling_lmp_id=h,
                        )
                        for name, h in zip(names, ids)
                    ]

                labelers = (
                    create_labelers(self.metrics.keys(), metrics_ids, EvaluationLabelerType.METRIC) +
                    create_labelers(self.annotations.keys(), annotation_ids, EvaluationLabelerType.ANNOTATION) +
                    (create_labelers(["criterion"], criteiron_ids, EvaluationLabelerType.CRITERION) if self.criterion else [])
                )

                # Add labelers to the serialized evaluation
                serialized_evaluation.labelers = labelers
                self.serialized = serialized_evaluation
                config.store.write_evaluation(serialized_evaluation)

        # Now serialize the evaluation run,
        evaluation_run.write(evaluation_id=self.id)

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
        lmp_params_with_invocation_id = {**lmp_params, "_get_invocation_id": True}
        lmp_output = self._get_lmp_output(data_point, lmp, lmp_params_with_invocation_id, required_params)

        if not isinstance(lmp_output, list):
            lmp_output = [cast(Any, lmp_output)]

        def process_rowar_results(output):
            def apply_labelers(labelers):
                return {
                    name: labeler(data_point, output[0], _get_invocation_id=True)
                    for name, labeler in labelers.items()
                }

            return _ResultDatapoint(
                output=output,
                metrics=apply_labelers(self.metrics),
                annotations=apply_labelers(self.annotations),
                criterion=apply_labelers({None: self.criterion})[None] if self.criterion else None
            )
            

        return [partial(process_rowar_results, output) for output in lmp_output]

    def _get_lmp_output(
        self,
        data_point: Datapoint,
        lmp: LMP,
        lmp_params: Dict[str, Any],
        required_params: bool,
    ) -> Union[List[Any], Any]:
        if not required_params:
            return lmp(**lmp_params)
        
        inp = data_point["input"]
        if isinstance(inp, list):
            return lmp(*inp, **lmp_params)
        elif isinstance(inp, dict):
            return lmp(**inp, **lmp_params)
        else:
            raise ValueError(f"Invalid input type: {type(inp)}")





