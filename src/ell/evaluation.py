from collections import defaultdict
from datetime import datetime
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
from tqdm import tqdm

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

    def summarize(self) -> Dict[str, float]:
        pass




class EvaluationRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    results : EvaluationResults = Field(default_factory=EvaluationResults)
    dataset : Optional[Dataset] = Field(default=None)
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
    dataset: Dataset
    metrics: Metrics = Field(default_factory=dict)
    annotations: Annotations = Field(default_factory=dict)
    criterion: Optional[Criterion] = None
    

    default_api_params: Optional[Dict[str, Any]] = Field(default_factory=dict)

    def write(self, serialized_evaluation_run) -> None:
        pass
   

    @field_validator('criterion')
    @classmethod
    def validate_criteria(cls, criteria: Union[Metric, List[Metrics]]) -> Metric:
        return _validate_callable_dict(criteria, "criterion")

    @field_validator('annotations')
    @classmethod
    def validate_annotations(cls, annotations: Union[Annotations, List[Annotation]]) -> Annotations:
        return _validate_callable_dict(annotations, "annotation")

    def run(self, lmp,  *, n_workers: int = 1, api_params: Optional[Dict[str, Any]] = None, verbose: bool = False, samples_per_datapoint: int = 1) -> EvaluationRun:
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
        run_api_params = {**(self.default_api_params or {}), **(api_params or {})}
        if samples_per_datapoint > 1:
            run_api_params['n'] = samples_per_datapoint
        lmp_to_use = lmp 
        
        evaluation_run = EvaluationRun(
            lmp=lmp_to_use,
            dataset=self.dataset,
            api_params=run_api_params,
            start_time=datetime.now()
        )

        original_verbose = config.verbose
        config.verbose = verbose
        try:
            
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                futures = [executor.submit(self._process_single, data_point, lmp_to_use, run_api_params) 
                           for data_point in self.dataset]
                
                desc = "Evaluating" 
                rowar_results = []
                with tqdm(total=len(self.dataset), desc=desc) as pbar:
                    for future in as_completed(futures):
                        result = future.result()
                        rowar_results.extend(result)
                        pbar.update(1)
                        

                        # Just show progress for optimization
                        pbar.set_postfix({'processed': len(rowar_results), 'most_recent_output': str(rowar_results[-1].output)[:10]})
            
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

    def _process_single(self, data_point: Datapoint, lmp: LMP, api_params: Dict[str, Any]) -> List[_ResultDatapoint]:
        """
        Process a single data point using the LMP and apply all criteria.
        
        Args:
            data_point (Any): A single item from the dataset.
            lmp (LMP): The LMP to use for processing.
            api_params (Dict[str, Any]): API parameters for this run.
        
        Returns:
            Tuple[List[Any], Dict[str, List[float]]]: The LMP outputs and a dictionary of scores from all metrics.
        """
        if isinstance(data_point['input'], list):
            lmp_output = lmp(*data_point['input'], api_params=api_params)
        elif isinstance(data_point['input'], dict):
            lmp_output = lmp(**data_point['input'], api_params=api_params)
        else:
            raise ValueError(f"Invalid input type: {type(data_point['input'])}")
        
        if not isinstance(lmp_output, list):
            lmp_output = [cast(Any, lmp_output)]
        
        return [
                _ResultDatapoint(
                    output=output,
                    metrics={name: float(metric(data_point, output)) for name, metric in self.metrics.items()},
                    annotations={name: annotation(data_point, output) for name, annotation in self.annotations.items()},
                    criterion=bool(self.criterion(data_point, output)) if self.criterion else None
                )
             for output in lmp_output]





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
    


