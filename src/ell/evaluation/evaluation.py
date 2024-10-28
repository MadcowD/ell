from datetime import datetime
from functools import partial
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    cast,
)
from concurrent.futures import ThreadPoolExecutor, as_completed
from ell.evaluation.results import _ResultDatapoint, EvaluationResults
from ell.evaluation.serialization import write_evaluation
from ell.evaluation.util import get_lmp_output
from ell.types.studio import LMPType

from ell.evaluation.util import validate_callable_dict

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ell.types.message import LMP
from ell.util.tqdm import tqdm
import inspect

from ell.util.closure_util import ido
from ell.util.closure_util import hsh

from ell.evaluation.results import *
import dill

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
        return [d.get("input", None) for d in self.dataset] if self.dataset else []

    @property
    def outputs(self) -> List[Any]:
        return self.results.outputs

    @property
    def invocation_ids(self) -> Optional[EvaluationResults[InvocationID]]:
        return self.results.invocation_ids

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
    has_serialized : bool = Field(default=False)

    id: Optional[str] = Field(default=None)
    @field_validator("id")
    def construct_id(self, v, values):
        # XXX: Figure this out.
        dataset_hash = hsh(str(dill.dumps(evaluation.dataset) if evaluation.dataset else str(evaluation.n_evals)) + str(evaluation.samples_per_datapoint))
        metrics_ids = [ido(f) for f in evaluation.metrics.values()]
        annotation_ids = [ido(a) for a in evaluation.annotations.values()]
        criteiron_ids = [ido(evaluation.criterion)] if evaluation.criterion else []
        
        return  "evaluation-" + hsh(dataset_hash + "".join(sorted(metrics_ids) + sorted(annotation_ids) + criteiron_ids))
        

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
        
        required_params, run_api_params, lmp_params = self.prepare_run_params(lmp, api_params, additional_lmp_params)
        dataset = self.prepare_run_dataset(use_api_batching, run_api_params)

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

            write_evaluation(self, evaluation_run)

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
        lmp_output = get_lmp_output(data_point, lmp, lmp_params_with_invocation_id, required_params)

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

    def prepare_run_params(self, lmp, api_params, additional_lmp_params):
        assert (
            "api_params" not in additional_lmp_params
        ), f"specify api_params directly to run not within additional_lmp_params: {additional_lmp_params}"
        # Inspect LMP signature to check for required arguments


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
        return required_params,run_api_params,lmp_params

    def prepare_run_dataset(self, use_api_batching, run_api_params):
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
            
        return dataset
    
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

    