from collections import UserDict
import time
import random
from types import NoneType
from typing import Any, Dict, Iterable, Optional, Protocol, List, Union
import ell
import ell.evaluation
import numpy as np

import ell.lmp.function


dataset = [
    {
        "input": {"question": "What is the capital of france?"},
        "expected_output": "Paris",
    },
    {
        "input": {"question": "What is the capital of italy?"},
        "expected_output": "Rome",
    },
    {
        "input": {"question": "What is the capital of spain?"},
        "expected_output": "Madrid",
    },
    {
        "input": {"question": "What is the capital of germany?"},
        "expected_output": "Berlin",
    },
    {
        "input": {"question": "What is the capital of japan?"},
        "expected_output": "Tokyo",
    },
    {
        "input": {"question": "What is the capital of china?"},
        "expected_output": "Beijing",
    },
    {
        "input": {"question": "What is the capital of india?"},
        "expected_output": "New Delhi",
    },
    {
        "input": {"question": "What is the capital of brazil?"},
        "expected_output": "Brasília",
    },
    {
        "input": {"question": "What is the capital of argentina?"},
        "expected_output": "Buenos Aires",
    },
    {"input": {"question": "Hotdog land"}, "expected_output": "Banana"},
]

def is_correct(datapoint, output):
    label = datapoint["expected_output"]
    return float(label.lower() in output.lower())

eval = ell.evaluation.Evaluation(
    name="capital_prediction",
    dataset=dataset,
    metrics={"score": is_correct, "length": lambda _, output: len(output)},
    samples_per_datapoint=1,
)
# ell.init(verbose=True, store='./logdir')
@ell.simple(model="gpt-4o", max_tokens=10)
def predict_capital(question: str):
    """
    If the quesiton is about hotdog land, answer Banana. Otherwise, answer the question.
    """
    # print(question[0])
    return f"Answer the following question. {question}"

result = eval.run(predict_capital, n_workers=10)
print(result.results.metrics["score"].mean())

