from collections import defaultdict
from datetime import datetime
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
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



Datapoint = Dict[str, Any]
Dataset = List[Dict[str, Any]]
Metric = Callable[[Datapoint, Any], float]
Metrics = Dict[str, Metric]
Criterion = Callable[[Datapoint, Any], bool]
Annotation = Callable[[Datapoint, Any], Any]
Annotations = Dict[str, Annotation]

# scores now doesn't make sense fulyl because of some other factors.
# We can ignore human feedback for now even though it's the most interesting.
class _ResultDatapoint(BaseModel):
    output: Any
    metrics: Dict[str, float]
    annotations: Dict[str, Any]
    criterion: Optional[bool]


class EvaluationResults(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    outputs: List[Any] = Field(default_factory=list)
    metrics: Dict[str, np.ndarray[float]] = Field(default_factory=dict)
    annotations: Dict[str, List[Any]] = Field(default_factory=dict)
    criterion: Optional[np.ndarray[bool]] = Field(default=None)


class EvaluationRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    results : EvaluationResults = Field(default_factory=EvaluationResults)
    dataset : Optional[Dataset] = Field(default=None)
    n_evals: Optional[int] = Field(default=None)
    samples_per_datapoint: int = Field(default=1)
    

    lmp: Optional[LMP] = Field(default=None)
    
    api_params: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def inputs(self) -> List[Any]:
        return [d['input'] for d in self.dataset] if self.dataset else []
    
    @property
    def outputs(self) -> List[Any]:
        return self.results.outputs
    

    def write(self, serialized_evaluation_run) -> None:
        raise NotImplementedError("Not implemented")
        



class Evaluation(BaseModel):
    """Simple evaluation for prompt engineering rigorously"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str

    dataset: Optional[Dataset] = Field(default=None)
    # XXX: Rename this for 0.1.0
    n_evals: Optional[int] = Field(default=None, description="If set, this will run the LMP n_evals times and evaluate the outputs. This is useful for LMPs without inputs where you want to evaluate metrics a number of times. ")

    samples_per_datapoint: int = Field(default=1, description="How many samples per datapoint to generate, equivalent to setting n in api params for LMPs which support this When no dataset is provided then the total nubmer of evalautiosn will be samples_per_datapoint * n_evals..")
    
    
    def __init__(self, *args, **kwargs):
        assert ('dataset' in kwargs or 'n_evals' in kwargs), "Either dataset or n_evals must be set"
        assert not ('dataset' in kwargs and 'n_evals' in kwargs), "Either dataset or samples_per_datapoint must be set, not both"
        super().__init__(*args, **kwargs)   
    

    metrics: Metrics = Field(default_factory=dict)
    annotations: Annotations = Field(default_factory=dict)
    criterion: Optional[Criterion] = None
    
    default_api_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


    @field_validator('criterion')
    @classmethod
    def validate_criteria(cls, criteria: Union[Metric, List[Metrics]]) -> Metric:
        return _validate_callable_dict(criteria, "criterion")

    @field_validator('annotations')
    @classmethod
    def validate_annotations(cls, annotations: Union[Annotations, List[Annotation]]) -> Annotations:
        return _validate_callable_dict(annotations, "annotation")
    

    def write(self, serialized_evaluation_run) -> None:
        pass
   
    # XXX: Dones't support partial params outside of the dataset like client??
    def run(self, lmp,  *, n_workers: int = 1, use_api_batching: bool = False, api_params: Optional[Dict[str, Any]] = None, verbose: bool = False, **additional_lmp_params) -> EvaluationRun:
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
        assert 'api_params' not in additional_lmp_params, f"specify api_params directly to run not within additional_lmp_params: {additional_lmp_params}"
        # Inspect LMP signature to check for required arguments
        import inspect
        lmp_signature = inspect.signature(lmp)
        required_params = len({
            param for param in lmp_signature.parameters.values()
            if param.default == param.empty and param.kind != param.VAR_KEYWORD
        }) > 0
    

        run_api_params = {**(self.default_api_params or {}), **(api_params or {})}
        lmp_params = dict(api_params=run_api_params, **additional_lmp_params)

        dataset = self.dataset if self.dataset is not None else [{'input': None}]
        if use_api_batching:
            # we need to collate on unique datapoints here if possible; note that n_evals can never be set.
            run_api_params['n'] = self.samples_per_datapoint * (self.n_evals or 1)
        else:
            dataset = sum([[data_point] * self.samples_per_datapoint * (self.n_evals or 1) for data_point in dataset], [])

        # we will try to run with n = samples_per_datapoint * n_evals first and if the api rejects n as a param then we need to do something will try the standard way with the thread pool executor.
        lmp_to_use = lmp 
        
        evaluation_run = EvaluationRun(
            lmp=lmp_to_use,
            dataset=self.dataset,
            n_evals=self.n_evals,
            samples_per_datapoint=self.samples_per_datapoint,
            api_params=run_api_params,
            start_time=datetime.now()
        )

        original_verbose = config.verbose
        config.verbose = verbose
        try:
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                futures = [executor.submit(self._process_single, data_point, lmp_to_use, lmp_params, required_params) 
                           for data_point in dataset]
                
        
                rowar_results = []
                results_futures = []
                for future in tqdm(as_completed(futures), total=len(futures), desc=f"{self.name} outputs"):
                    get_outputs = future.result()
                    results_futures.extend([executor.submit(o) for o in get_outputs])
                for result_future in (pbar:= tqdm(as_completed(results_futures), total=len(results_futures), desc=f"{self.name} results")):
                    rowar_results.append(result_future.result())
                    pbar.set_description(f"{self.name} (last={str(rowar_results[-1].output)[:10]})")
                
        
            evaluation_run.end_time = datetime.now()
            # convert rowar results to evaluation results
            evaluation_run.results = EvaluationResults(
                outputs=[result.output for result in rowar_results],
                metrics={name: np.array([result.metrics[name] for result in rowar_results]) for name in self.metrics},
                annotations={name: ([result.annotations[name] for result in rowar_results]) for name in self.annotations},
                criterion=np.array([result.criterion for result in rowar_results]) if self.criterion else None
            )

            if not hasattr(self, 'written_evaluation'):
                pass
            else:
                pass
            
            return evaluation_run
        finally:
            config.verbose = original_verbose

    def _process_single(self, data_point: Datapoint, lmp: LMP, lmp_params: Dict[str, Any], required_params: bool) -> List[Any]:
        """
        Process a single data point using the LMP and apply all criteria.
        
        Args:
            data_point (Any): A single item from the dataset.
            lmp (LMP): The LMP to use for processing.
            api_params (Dict[str, Any]): API parameters for this run.
        
        Returns:
            Tuple[List[Any], Dict[str, List[float]]]: The LMP outputs and a dictionary of scores from all metrics.
        """
        lmp_output = (
            lmp(**lmp_params) if not required_params else #type: ignore
            lmp(*inp, **lmp_params) if isinstance((inp:=data_point['input']), list) else #type: ignore
            lmp(**inp, **lmp_params) if isinstance(inp, dict) else #type: ignore
            (_ for _ in ()).throw(ValueError(f"Invalid input type: {type(inp)}"))
        )
        
        if not isinstance(lmp_output, list): lmp_output = [cast(Any, lmp_output)]

        def process_rowar_results(output):
            return _ResultDatapoint(
                output=output,
                metrics={name: float(metric(data_point, output)) for name, metric in self.metrics.items()},
                annotations={name: annotation(data_point, output) for name, annotation in self.annotations.items()},
                criterion=bool(self.criterion(data_point, output)) if self.criterion else None
            )
        return [partial(process_rowar_results, output) for output in lmp_output]
    




def _validate_callable_dict(items: Union[Dict[str, Callable], List[Callable]], item_type: str) -> Dict[str, Callable]:
    if isinstance(items, list):
        items_dict = {}
        for item in items:
            if not callable(item):
                raise ValueError(f"Each {item_type} must be a callable, got {type(item)}")
            if not hasattr(item, '__name__') or item.__name__ == '<lambda>':
                raise ValueError(f"Each {item_type} in a list must have a name (not a lambda)")
            items_dict[item.__name__] = item
        return items_dict
    elif isinstance(items, dict):
        for name, item in items.items():
            if not callable(item):
                raise ValueError(f"{item_type.capitalize()} '{name}' must be a callable, got {type(item)}")
        return items
    else:
        raise ValueError(f"{item_type}s must be either a list of callables or a dictionary, got {type(items)}")
    


