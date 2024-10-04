from datetime import datetime
from typing import Any, Callable, Iterable, Dict, List, Optional, Protocol, Tuple, TypedDict, Union, cast
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

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




# Or we'll actually do a datamodel from pydanytic. Not sure I like this.

Datapoint = Dict[str, Any]
Dataset = List[Dict[str, Any]]
Criterion = Callable[[Datapoint, Any], float]


class EvaluationRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    scores: Optional[List[float]] = None
    inputs: List[Any] = Field(default_factory=list)
    lmp: Optional[LMP] = Field(default=None)
    outputs: List[Any] = Field(default_factory=list)
    api_params: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def write(self, serialized_evaluation) -> None:
        # To link!

        pass

class Evaluation(BaseModel):
    """Simple evaluation for prompt engineering rigorously"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    dataset: Dataset
    criterion: Optional[List[Criterion]] = Field(default_factory=list)
    default_api_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


    @field_validator('dataset')
    def validate_dataset(cls, dataset: Dataset) -> Dataset:
        for datapoint in dataset:
            if not isinstance(datapoint, dict):
                raise ValueError(f"Each datapoint must be a dictionary, got {type(datapoint)}")
            if "input" not in datapoint:
                raise ValueError("Each datapoint must have an 'input' key", datapoint)
            if not isinstance(datapoint["input"], (list, dict)):
                raise ValueError(f"The 'input' value must be a list or dictionary, got {type(datapoint['input'])}", datapoint)
            if not isinstance(datapoint["input"], (list, dict)):
                raise ValueError(f"The 'input' value must be a list or dictionary, got {type(datapoint['input'])}", datapoint)
        return dataset

    @field_validator('criterion')
    def validate_criterion(cls, criterion: List[Criterion]) -> List[Criterion]:
        for crit in criterion:
            if not callable(crit):
                raise ValueError(f"Each criterion must be a callable, got {type(crit)}")
        return criterion
    
    # def write(self) -> SerializedEvaluation:
    #     criterion_src = []
    #     criterion_dep_src = []
    #     for crit in self.criterion:
    #         src = lexical_closure(crit, initial_call=True)
    #         crit_src, crit_dep_src = src[1]
    #         criterion_src.append(crit_src)
    #         criterion_dep_src.append(crit_dep_src)

    #     dataset_pickle = dill.dumps(self.dataset)
    #     dataset_id = hashlib.md5(dataset_pickle).hexdigest()

    #     serialized_evaluation = SerializedEvaluation(
    #         name=self.name,
    #         criterion_src=criterion_src,
    #         criterion_dependencies_src=criterion_dep_src,
    #         default_api_params=self.default_api_params,
    #         has_criterion=len(self.criterion) > 0,
    #         num_datapoints=len(self.dataset), 
    #         version_number=None,
    #         created_at=datetime.now(),
    #         id= "evaluation-" + hashlib.md5(
    #         f"{criterion_src}{criterion_dep_src}{self.default_api_params}{dataset_id}".encode()
    #     ).hexdigest()
    #     )

    #     self.written_evaluation = serialized_evaluation
    #     return serialized_evaluation
        
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
            results = []
            outputs = []
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                futures = [executor.submit(self._process_single, data_point, lmp_to_use, run_api_params, samples_per_datapoint) 
                           for data_point in self.dataset]
                
                desc = "Evaluating" 
                with tqdm(total=len(self.dataset), desc=desc) as pbar:
                    for future in as_completed(futures):
                        output, result = future.result()
                        results.extend(result)  # Extend with the 2D array of scores
                        outputs.extend(output)  # Extend instead of append
                        pbar.update(1)
                        
                        if self.criterion:
                            # Update moving statistics for evaluation
                            num_criteria = len(self.criterion)
                            flat_results = [score for sample_scores in results for score in sample_scores]
                            current_means = [statistics.mean(flat_results[i::num_criteria]) for i in range(num_criteria)]
                            current_medians = [statistics.median(flat_results[i::num_criteria]) for i in range(num_criteria)]
                            current_mins = [min(flat_results[i::num_criteria]) for i in range(num_criteria)]
                            current_maxs = [max(flat_results[i::num_criteria]) for i in range(num_criteria)]
                            
                            pbar.set_postfix({
                                'means': [f'{m:.4f}' for m in current_means],
                                'medians': [f'{m:.4f}' for m in current_medians],
                                'mins': [f'{m:.4f}' for m in current_mins],
                                'maxs': [f'{m:.4f}' for m in current_maxs],
                                'most_recent_output': str(output[0])[:10]
                            })
                        else:
                            # Just show progress for optimization
                            pbar.set_postfix({'processed': len(results), 'most_recent_output': str(output[0])[:10]})
            
            evaluation_run.outputs = outputs
            if self.criterion:
                evaluation_run.scores = np.array(results)
            evaluation_run.end_time = datetime.now()

            if not hasattr(self, 'written_evaluation'):
                # serialized_evaluation = self.write()
                pass
            else:
                # serialized_evaluation = self.written_evaluation
                pass
            # evaluation_run.write(serialized_evaluation)
            
            return evaluation_run
        finally:
            config.verbose = original_verbose
            
    def _process_single(self, data_point: Datapoint, lmp: LMP, api_params: Dict[str, Any], samples_per_datapoint: int) -> Tuple[List[Any], List[List[float]]]:
        """
        Process a single data point using the LMP and apply all criteria.
        
        Args:
            data_point (Any): A single item from the dataset.
            lmp (LMP): The LMP to use for processing.
            api_params (Dict[str, Any]): API parameters for this run.
            samples_per_datapoint (int): Number of samples to generate per datapoint.
        
        Returns:
            Tuple[List[Any], List[List[float]]]: The LMP outputs and a 2D array of scores from all criteria.
        """
        if isinstance(data_point['input'], list):
            lmp_output = lmp(*data_point['input'], api_params=api_params)
        elif isinstance(data_point['input'], dict):
            lmp_output = lmp(**data_point['input'], api_params=api_params)
        else:
            raise ValueError(f"Invalid input type: {type(data_point['input'])}")
        
        if not isinstance(lmp_output, list):
            lmp_output = [lmp_output]
        
        if self.criterion:
            scores = [
                [float(crit(data_point, output)) for crit in self.criterion]
                for output in lmp_output
            ]
            return lmp_output, scores
        return lmp_output, [[]] * len(lmp_output)  # Return empty scores if no criterion
