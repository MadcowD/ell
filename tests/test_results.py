from ell.evaluation.results import _ResultDatapoint, EvaluationResults


def test_evaluation_results_from_rowar_results():
    # Test that from_rowar_results correctly converts rowar_results to EvaluationResults
    rowar_results = [
        _ResultDatapoint(
            output=("output1", "id1"),
            metrics={"metric1": (0.95, "id1")},
            annotations={"annotation1": ("anno1", "id1")},
            criterion=(True, "id1")
        ),
        _ResultDatapoint(
            output=("output2", "id2"),
            metrics={"metric1": (0.85, "id2")},
            annotations={"annotation1": ("anno2", "id2")},
            criterion=(False, "id2")
        ),
    ]
    results = EvaluationResults.from_rowar_results(rowar_results)
    
    assert results.outputs == ["output1", "output2"]
    assert (results.metrics["metric1"] == [0.95, 0.85]).all()
    assert results.annotations["annotation1"] == ["anno1", "anno2"]
    assert results.criterion == [True, False]
    
    # Check invocation_ids
    assert results.invocation_ids is not None
    assert results.invocation_ids.outputs == ["id1", "id2"]
    assert (results.invocation_ids.metrics["metric1"] == ["id1", "id2"])
    assert results.invocation_ids.annotations["annotation1"] == ["id1", "id2"]
    assert results.invocation_ids.criterion == ["id1", "id2"]
