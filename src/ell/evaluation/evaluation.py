from dataclasses import field
import dataclasses
from datetime import datetime, timezone
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
from ell.evaluation.serialization import write_evaluation, write_evaluation_run_end, write_evaluation_run_intermediate, write_evaluation_run_start
from ell.evaluation.util import get_lmp_output
from ell.stores.models import LMPType

from ell.evaluation.util import validate_callable_dict

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ell.types.message import LMP
from ell.stores.models.evaluations import EvaluationLabelerType
from ell.util.tqdm import tqdm
import inspect

from ell.util.closure_util import ido
from ell.util.closure_util import hsh

from ell.configurator import config
from ell.evaluation.results import *

@dataclass
class EvaluationRun:
    results: EvaluationResults = field(default_factory=EvaluationResults)
    dataset: Optional[Dataset] = field(default=None)
    n_evals: Optional[int] = field(default=None)
    samples_per_datapoint: int = field(default=1)
    lmp: Optional[LMP] = field(default=None)
    api_params: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = field(default=None)
    end_time: Optional[datetime] = field(default=None)
    id: Optional[str] = field(default=None)
    success: Optional[bool] = field(default=None)
    error: Optional[str] = field(default=None)

    @property
    def inputs(self) -> List[Any]:
        return [d.get("input", None) for d in self.dataset] if self.dataset else []

    @property
    def outputs(self) -> List[Any]:
        return self.results.outputs

    @property
    def invocation_ids(self) -> Optional[EvaluationResults[InvocationID]]:
        return self.results.invocation_ids


class Evaluation(LabelListMixin):
    def __init__(self, name: str, *, metrics=None, annotations=None, criterion=None, 
                 dataset=None, n_evals=None, samples_per_datapoint=1,
                 default_api_params=None, has_serialized=False, id=None):
        """Initialize with both class fields and additional parameters"""
        self.name = name
        self.dataset = dataset
        self.n_evals = n_evals
        self.samples_per_datapoint = samples_per_datapoint
        self.labels: List[Labeler] = []
        self.default_api_params = default_api_params or {}
        self.has_serialized = has_serialized
        self.id = id

        from ell.lmp.function import function

        def wrap_callable(value):
            if isinstance(value, dict):
                return {
                    k: (
                        function(type=LMPType.LABELER)(v)
                        if callable(v) and not hasattr(v, "__ell_track__")
                        else v
                    )
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                return [
                    function(type=LMPType.LABELER)(v)
                    if callable(v) and not hasattr(v, "__ell_track__")
                    else v
                    for v in value
                ]
            elif callable(value) and not hasattr(value, "__ell_track__"):
                return function()(value)
            elif value is None:
                return value
            else:
                raise ValueError(f"Expected dict, list, callable, or None, got {type(value)}")

        # Validate dataset/n_evals
        if self.dataset is None and self.n_evals is None:
            raise ValueError("Either dataset or n_evals must be set")
        if self.dataset is not None and self.n_evals is not None:
            raise ValueError("Either dataset or n_evals must be set, not both")

        # Wrap and validate metrics/annotations/criterion
        metrics = validate_callable_dict(wrap_callable(metrics), "metric") if metrics else None
        annotations = validate_callable_dict(wrap_callable(annotations), "annotation") if annotations else None
        criterion = wrap_callable(criterion)


        # Convert to labelers
        self.labels = []
        if metrics:
            self.labels.extend([
                Labeler(name=name, type=EvaluationLabelerType.METRIC, label=labeler)
                for name, labeler in metrics.items()
            ])
        if annotations:
            self.labels.extend([
                Labeler(name=name, type=EvaluationLabelerType.ANNOTATION, label=labeler)
                for name, labeler in annotations.items()
            ])
        if criterion:
            self.labels.append(
                Labeler(name="criterion", type=EvaluationLabelerType.CRITERION, label=criterion)
            )
        assert len(self.labels) > 0, "No labels found, labeless evaluations coming soon! Specify metrics, annotations, or criterion."
        assert not annotations, "Annotations are not supported yet."


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

        assert len(dataset) > 0, "Dataset must contain at least one datapoint"

        evaluation_run = EvaluationRun(
            lmp=lmp,
            dataset=self.dataset,
            n_evals=self.n_evals,
            samples_per_datapoint=self.samples_per_datapoint,
            api_params=run_api_params,
            start_time=datetime.now(timezone.utc),
        )
        original_verbose = config.verbose
        config.verbose = verbose
        rowar_results = []
        
        write_evaluation(self)
        evaluation_run.id = write_evaluation_run_start(self, evaluation_run)
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

                    def written_result(o):
                        write_evaluation_run_intermediate(self, evaluation_run, (res := o()))
                        return res
                
                    metric_futures.extend([executor.submit(written_result, o) for o in get_outputs])

                for result_future in (
                    pbar := tqdm(
                        as_completed(metric_futures),
                        total=len(metric_futures),
                        desc=f"{self.name} results",
                    )
                ):
                    # We write the evaluation after the first datapoint.
                    rowar_results.append((res :=result_future.result()))
                    pbar.set_description(
                        f"{self.name} (last={str(rowar_results[-1].output)[:10]})"
                    )

            evaluation_run.end_time = datetime.now(timezone.utc)
            evaluation_run.success = True

            # Still want to compute metrics.
            evaluation_run.results = EvaluationResults.from_rowar_results(rowar_results)
            write_evaluation_run_end(self, evaluation_run)

            return evaluation_run
            # TODO: add error handling and unsccessful runs.
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
            return _ResultDatapoint(
                output=output,
                labels=[
                    Label(name=l.name, type=l.type, label=(l.label(data_point, output[0], _get_invocation_id=True)))
                    for l in self.labels
                ]
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
                ], []
            )
            
        return dataset
