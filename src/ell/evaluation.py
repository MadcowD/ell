from datetime import datetime
from typing import Any, Callable, Iterable, Dict, List, Optional, cast
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel._compat import SQLModelConfig
from ell.lmp._track import _track
from ell.types.message import LMP
import statistics
from tqdm import tqdm

import contextlib
import dill
import hashlib

from ell.configurator import config
from ell.types.studio import SerializedEvaluation
from ell.util.closure import lexical_closure, lexically_closured_source



Metric = Callable[..., float]


 #XXX: Seperate this into VersionedEvaluation and Evaluation because versioning is somewhat expensive if someone has a big eval Then perhaps we could default to VersionedEval in the docs or version=False. Not sure.
 # TODO: Link Invocations to EvalRuns
 # TODO: Link Invocations to INvocationScores.
 # TODO: Write to DB
 # TODO: Build UX for analyzing evals.
 # TODO: Solve (input, labels, score_fn) etc
 # TODO: What about automatic cross validation & splitting.

 # TODO: Consider wandb style metrics later.


class EvaluationRun(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    scores: Optional[List[float]] = None
    inputs: List[Any] = Field(default_factory=list)
    lmp: Optional[LMP] = Field(default=None)
    outputs: List[Any] = Field(default_factory=list)
    api_params: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def write(self, serialized_evaluation: SerializedEvaluation) -> None:
        # To link!

        pass


class Evaluation(BaseModel):
    """Evals or optimizes LMPs over a dataset."""
    model_config =  ConfigDict(arbitrary_types_allowed=True)
    dataset : List[Any]
    lmp : Optional[LMP] = Field(default=None)
    metric : Optional[Metric] = Field(default=None)
    default_api_params : Dict[str, Any] = Field(default=None)
    name : str
    written_evaluation : Optional[SerializedEvaluation] = Field(default=None)


    def write(self) -> SerializedEvaluation:
        if self.metric is not None:
            src = lexical_closure(self.metric, initial_call=True)
            metric_src, metric_dep_src = src[1]
        else:
            metric_src = None
            metric_dep_src = None

        datasetID = "TODO WRITE DATASET TO PICKLE DUMP"
        dataset_pickle =dill.dumps(self.dataset)
        dataset_id = hashlib.md5(dataset_pickle).hexdigest()

        serialized_evaluation = SerializedEvaluation(
            name=self.name,
            metric_src=metric_src,
            metric_dependencies_src=metric_dep_src,
            default_api_params=self.default_api_params,
            has_metric=self.metric is not None, num_datapoints=len(self.dataset), 
            version_number=None,
            created_at=datetime.now(),
            id= "evaluation-" + hashlib.md5(
            f"{metric_src}{metric_dep_src}{self.default_api_params}{dataset_id}".encode()
        ).hexdigest()
        )

        self.written_evaluation = serialized_evaluation
        return serialized_evaluation
        
   

    def run(self, lmp: Optional[LMP] = None,  *, n_workers: int = 1, api_params: Optional[Dict[str, Any]] = None, verbose: bool = False) -> EvaluationRun:
        """
        Run the evaluation or optimization using the specified number of workers.
        
        Args:
            n_workers (int): Number of parallel workers to use. Default is 1.
            lmp (Optional[LMP]): LMP to use for this run. If None, uses the LMP set during initialization.
            api_params (Dict[str, Any]): API parameters to override defaults.
            verbose (bool): Whether to run in verbose mode. Default is False.
        
        Returns:
            EvaluationRun: Object containing statistics about the evaluation or optimization outputs.
        """
        run_api_params = {**(self.default_api_params or {}), **(api_params or {})}
        lmp_to_use = lmp or self.lmp
        
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
                futures = [executor.submit(self._process_single, data_point, lmp_to_use, run_api_params) 
                           for data_point in self.dataset]
                
                desc = "Evaluating" 
                with tqdm(total=len(self.dataset), desc=desc) as pbar:
                    for future in as_completed(futures):
                        output, result = future.result()
                        results.append(result)
                        outputs.append(output)
                        pbar.update(1)
                        
                        if self.metric:
                            # Update moving statistics for evaluation
                            current_mean = statistics.mean(results)
                            current_median = statistics.median(results)
                            current_min = min(results)
                            current_max = max(results)
                            
                            pbar.set_postfix({
                                'mean': f'{current_mean:.4f}',
                                'median': f'{current_median:.4f}',
                                'min': f'{current_min:.4f}',
                                'max': f'{current_max:.4f}',
                                'most_recent_output': str(output)[:10]
                            })
                        else:
                            # Just show progress for optimization
                            pbar.set_postfix({'processed': len(results), 'most_recent_output': str(output)[:10]})
            
            evaluation_run.outputs = outputs
            if self.metric:
                evaluation_run.scores = results
            evaluation_run.end_time = datetime.now()

            # Todo: 
            if not self.written_evaluation: #and config.store is not None:
                serialized_evaluation = self.write()
            else:
                serialized_evaluation = self.written_evaluation
            evaluation_run.write(serialized_evaluation)
            
            return evaluation_run
        finally:
            config.verbose = original_verbose
            

    def _process_single(self, data_point: Any, lmp: LMP, api_params: Dict[str, Any]) -> Any:
        """
        Process a single data point using the LMP and optionally apply the metric.
        
        Args:
            data_point (Any): A single item from the dataset.
            lmp (LMP): The LMP to use for processing.
            api_params (Dict[str, Any]): API parameters for this run.
        
        Returns:
            Any: The metric score if metric is provided, otherwise the LMP output.
        """
        lmp_output = lmp(data_point, api_params=api_params)
        if self.metric:
            return lmp_output, self.metric(data_point, lmp_output)
        return lmp_output, 0