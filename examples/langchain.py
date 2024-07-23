
import ell

import random
import numpy as np

from ell.stores.sql import SQLiteStore

ell.config.verbose = True

@ell.lm(model="gpt-4o-mini")
def come_up_with_a_premise_for_a_joke_about(topic : str):
    """You are an incredibly talented comedian. Come up with a premise for a joke about topic"""
    return f"come up with a premise for a joke about {topic}"


def get_random_length():
    return int(np.random.beta(2, 5) * 1000)


@ell.lm(model="gpt-4o")
def joke(topic : str):
    """You are an incredibly talented comedian. You respond in scripts."""
    return f"Act out a full joke. Make your script {get_random_length()} words long. Here's the premise: {come_up_with_a_premise_for_a_joke_about(topic)}"


if __name__ == "__main__":
    store = SQLiteStore('sqlite_example')
    store.install()
    come_up_with_a_premise_for_a_joke_about("minecraft") # <The joke>