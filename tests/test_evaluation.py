import pytest

import ell.lmp.function
from datetime import datetime
from ell.evaluation.evaluation import Evaluation, EvaluationRun
from ell.evaluation.results import EvaluationResults
from ell.configurator import config

# Mock classes and functions
@ell.lmp.function.function()
def MockLMP(param=None, api_params=None):
    return "mock_output"

@ell.lmp.function.function()
def paramless(api_params=None):
    return "mock_output"

@pytest.fixture
def mock_evaluation():
    return Evaluation(
        name="test_evaluation",
        n_evals=10,
        samples_per_datapoint=2,
        metrics={"mock_metric": lambda x, y: 1.0},
        # annotations={"mock_annotation": lambda x, y: "annotation"},
        criterion=lambda x, y: True
    )


def test_evaluation_initialization(mock_evaluation):
    assert mock_evaluation.name == "test_evaluation"
    assert mock_evaluation.n_evals == 10
    assert mock_evaluation.samples_per_datapoint == 2
    assert "mock_metric" in mock_evaluation.metrics
    # assert "mock_annotation" in mock_evaluation.annotations


def test_evaluation_run_process_single(mock_evaluation):
    data_point = {"input": {"param": "test_input"}}
    lmp = MockLMP
    required_params = False

    results = mock_evaluation._process_single(data_point, lmp, {}, required_params)
    assert len(results) == 1
    assert results[0]().output[0] == "mock_output"

def test_evaluation_run(mock_evaluation):
    lmp = paramless

    evaluation_run = mock_evaluation.run(lmp, n_workers=1, verbose=False)
    assert evaluation_run.n_evals == 10
    assert evaluation_run.samples_per_datapoint == 2

def test_evaluation_run_with_different_inputs(mock_evaluation):
    # Test with list input
    data_point = {"input": ["test_input1", "test_input2"]}
    lmp = MockLMP
    lmp_params = {}
    required_params = True

    results = mock_evaluation._process_single(data_point, lmp, lmp_params, required_params)
    assert len(results) == 1
    assert results[0]().output[0] == "mock_output"

    # Test with no input
    data_point = {}
    results = mock_evaluation._process_single(data_point, lmp, lmp_params, required_params)
    assert len(results) == 1
    assert results[0]().output[0] == "mock_output"

def test_evaluation_run_with_invalid_input(mock_evaluation):
    data_point = {"input": 123}  # Invalid input type
    lmp = MockLMP
    required_params = True

    with pytest.raises(ValueError, match="Invalid input type: <class 'int'>"):
        mock_evaluation._process_single(data_point, lmp, {}, required_params)

def test_evaluation_run_with_missing_params(mock_evaluation):
    data_point = {"input": {"param": "test_input"}}
    lmp = MockLMP
    lmp_params = {}  # Missing required params
    required_params = False

    results = mock_evaluation._process_single(data_point, lmp, lmp_params, required_params)
    assert len(results) == 1
    assert results[0]().output[0] == "mock_output"


def test_evaluation_run_with_criterion(mock_evaluation):
    # Test with a criterion
    data_point = {"input": {"param": "test_input"}}
    lmp = MockLMP
    required_params = False

    results = mock_evaluation._process_single(data_point, lmp, {}, required_params)
    assert len(results) == 1
    assert results[0]().criterion[0] == True



