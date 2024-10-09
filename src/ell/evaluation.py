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
Metrics = Callable[[Datapoint, Any], float]
Metric = Dict[str, Metrics]
Criterion = Callable[[Datapoint, Any], bool]
Annotation = Callable[[Datapoint, Any], Any]
Annotations = Dict[str, Annotation]



class EvaluationRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    scores: Dict[str, List[float]] = Field(default_factory=dict)
    dataset : Dataset = Field(default_factory=list)
    lmp: Optional[LMP] = Field(default=None)
    outputs: List[Any] = Field(default_factory=list)
    api_params: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def inputs(self) -> List[Any]:
        return [d['input'] for d in self.dataset]
    

    def write(self, serialized_evaluation_run) -> None:
        # To link!
        pass

class Evaluation(BaseModel):
    """Simple evaluation for prompt engineering rigorously"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    dataset: Dataset
    # I htink we should jsut basically have one field so as to not overload this
    metrics: Optional[Metric] = Field(default_factory=dict)
    criterion: Optional[Criterion] = None
    annotations : Optional[Annotations] = Field(default_factory=dict)

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
            inputs=self.dataset,
            api_params=run_api_params,
            start_time=datetime.now()
        )

        original_verbose = config.verbose
        config.verbose = verbose
        try:
            scores : Dict[str, List[float]] = defaultdict(list)
            outputs = []
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                futures = [executor.submit(self._process_single, data_point, lmp_to_use, run_api_params) 
                           for data_point in self.dataset]
                
                desc = "Evaluating" 
                with tqdm(total=len(self.dataset), desc=desc) as pbar:
                    for future in as_completed(futures):
                        output, result = future.result()
                        for name, value in result.items():
                            scores[name].extend(value)
                        outputs.extend(output)  # Extend instead of append
                        pbar.update(1)
                        
                        if self.metrics:
                            # Update moving statistics for evaluation
                            current_means = {name: statistics.mean(scores[name]) for name in self.metrics}
                            
                            pbar.set_postfix({
                                'means': {name: f'{value:.4f}' for name, value in current_means.items()},
                                'most_recent_output': str(output[0])[:10]
                            })
                        else:
                            # Just show progress for optimization
                            pbar.set_postfix({'processed': len(outputs), 'most_recent_output': str(output[0])[:10]})
            
            evaluation_run.outputs = outputs
            if self.metrics:
                evaluation_run.scores = scores  # Store the list of score dictionaries directly
            evaluation_run.end_time = datetime.now()

            if not hasattr(self, 'written_evaluation'):
                pass
            else:
                pass
            
            return evaluation_run
        finally:
            config.verbose = original_verbose
            
    def _process_single(self, data_point: Datapoint, lmp: LMP, api_params: Dict[str, Any]) -> Tuple[List[Any], Dict[str, List[float]]]:
        """
        Process a single data point using the LMP and apply all criteria.
        
        Args:
            data_point (Any): A single item from the dataset.
            lmp (LMP): The LMP to use for processing.
            api_params (Dict[str, Any]): API parameters for this run.
            samples_per_datapoint (int): Number of samples to generate per datapoint.
        
        Returns:
            Tuple[List[Any], List[Dict[str, float]]]: The LMP outputs and a 2D array of scores from all criteria.
        """
        if isinstance(data_point['input'], list):
            lmp_output = lmp(*data_point['input'], api_params=api_params)
        elif isinstance(data_point['input'], dict):
            lmp_output = lmp(**data_point['input'], api_params=api_params)
        else:
            raise ValueError(f"Invalid input type: {type(data_point['input'])}")
        
        if not isinstance(lmp_output, list):
            lmp_output = [cast(Any, lmp_output)]
        
        if self.metrics:
            scores = {
                name: [
                    float(crit(data_point, output)) for output in lmp_output 
                ] for name, crit in self.metrics.items()
            }
            return lmp_output, scores
        return lmp_output, {}  # Return empty score dicts if no criteria




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