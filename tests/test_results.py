from ell.evaluation.results import _ResultDatapoint, EvaluationResults, Label
from ell.stores.models.evaluations import EvaluationLabelerType
import numpy as np

def test_evaluation_results_from_rowar_results():
    # Test that from_rowar_results correctly converts rowar_results to EvaluationResults
    rowar_results = [
        _ResultDatapoint(
            output=("output1", "id1"),
            labels=[
                Label(name="metric1", type=EvaluationLabelerType.METRIC, label=(0.95, "id1")),
                Label(name="annotation1", type=EvaluationLabelerType.ANNOTATION, label=("anno1", "id1")),
                Label(name="criterion", type=EvaluationLabelerType.CRITERION, label=(True, "id1"))
            ]
        ),
        _ResultDatapoint(
            output=("output2", "id2"),
            labels=[
                Label(name="metric1", type=EvaluationLabelerType.METRIC, label=(0.85, "id2")),
                Label(name="annotation1", type=EvaluationLabelerType.ANNOTATION, label=("anno2", "id2")),
                Label(name="criterion", type=EvaluationLabelerType.CRITERION, label=(False, "id2"))
            ]
        ),
    ]
    results = EvaluationResults.from_rowar_results(rowar_results)
    
    assert results.outputs == ["output1", "output2"]
    assert (results.metrics["metric1"] == np.array([0.95, 0.85])).all()
    assert (results.annotations["annotation1"] == np.array(["anno1", "anno2"])).all()
    assert (results.criterion == np.array([True, False])).all()
    
    # Check invocation_ids
    assert results.invocation_ids is not None
    assert results.invocation_ids.outputs == ["id1", "id2"]
    assert (results.invocation_ids.metrics["metric1"] == np.array(["id1", "id2"])).all()
    assert (results.invocation_ids.annotations["annotation1"] == np.array(["id1", "id2"])).all()
    assert (results.invocation_ids.criterion == np.array(["id1", "id2"])).all()
