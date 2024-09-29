from typing import Any, Callable, Iterable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from ell.types.message import LMP
import statistics
from tqdm import tqdm
import ell.config
import contextlib
import dill
import hashlib

Metric = Callable[..., float]

class EvaluationResult:
    def __init__(self, scores: Optional[List[float]] = None, outputs: Optional[List[Any]] = None):
        self.scores = scores
        self.outputs = outputs
        if scores:
            self.mean = statistics.mean(scores)
            self.median = statistics.median(scores)
            self.stdev = statistics.stdev(scores) if len(scores) > 1 else 0
            self.min = min(scores)
            self.max = max(scores)

    def __str__(self):
        if self.scores:
            return (f"EvaluationResult(mean={self.mean:.4f}, median={self.median:.4f}, "
                    f"stdev={self.stdev:.4f}, min={self.min:.4f}, max={self.max:.4f})")
        else:
            return f"OptimizationResult(outputs={len(self.outputs)} items)"

class Evaluation:
    """Evals or optimizes LMPs over a dataset."""

    def __init__(self, dataset: Iterable, lmp: LMP, metric: Optional[Metric] = None, default_api_params: Dict[str, Any] = None):
        self.dataset = list(dataset)  # Convert to list to get length for tqdm
        self.lmp = lmp
        self.metric = metric
        self.default_api_params = default_api_params or {}
        self._version = self._compute_version()

    @property
    def version(self) -> str:
        """Read-only version property based on the current state of the Evaluation object."""
        return self._version

    def _compute_version(self) -> str:
        """Compute a version hash based on the current state of the Evaluation object."""
        state = dill.dumps((self.lmp, self.metric, self.default_api_params))
        return hashlib.md5(state).hexdigest()

    def serialize(self, filename: str) -> None:
        """Serialize the Evaluation object to a file."""
        with open(filename, 'wb') as f:
            dill.dump(self, f)

    @staticmethod
    def deserialize(filename: str) -> 'Evaluation':
        """Deserialize an Evaluation object from a file."""
        with open(filename, 'rb') as f:
            return dill.load(f)

    @contextlib.contextmanager
    def _temp_verbose(self, verbose: bool):
        """Temporarily set ell.config.verbose"""
        original_verbose = ell.config.verbose
        ell.config.verbose = verbose
        try:
            yield
        finally:
            ell.config.verbose = original_verbose

    def run(self, n_workers: int = 1, api_params: Dict[str, Any] = None, verbose: bool = False) -> EvaluationResult:
        """
        Run the evaluation or optimization using the specified number of workers.
        
        Args:
            n_workers (int): Number of parallel workers to use. Default is 1.
            api_params (Dict[str, Any]): API parameters to override defaults.
            verbose (bool): Whether to run in verbose mode. Default is False.
        
        Returns:
            EvaluationResult: Object containing statistics about the evaluation or optimization outputs.
        """
        run_api_params = {**self.default_api_params, **(api_params or {})}
        
        with self._temp_verbose(verbose):
            results = []
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                futures = [executor.submit(self._process_single, data_point, run_api_params) 
                           for data_point in self.dataset]
                
                desc = "Evaluating" if self.metric else "Optimizing"
                with tqdm(total=len(self.dataset), desc=desc, disable=not verbose) as pbar:
                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
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
                                'max': f'{current_max:.4f}'
                            })
                        else:
                            # Just show progress for optimization
                            pbar.set_postfix({'processed': len(results)})
            
            if self.metric:
                return EvaluationResult(scores=results)
            else:
                return EvaluationResult(outputs=results)

    def _process_single(self, data_point: Any, api_params: Dict[str, Any]) -> Any:
        """
        Process a single data point using the LMP and optionally apply the metric.
        
        Args:
            data_point (Any): A single item from the dataset.
            api_params (Dict[str, Any]): API parameters for this run.
        
        Returns:
            Any: The metric score if metric is provided, otherwise the LMP output.
        """
        lmp_output = self.lmp(data_point, api_params=api_params)
        if self.metric:
            return self.metric(data_point, lmp_output)
        return lmp_output