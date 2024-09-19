
import ell

import random
import numpy as np

from ell.stores.sql import SQLiteStore

@ell.simple(model="gpt-4o-mini")
def come_up_with_a_premise_for_a_joke_about(topic : str):
    """You are an incredibly funny comedian. Come up with a premise for a joke about topic"""
    return f"come up with a premise for a joke about {topic}"


def get_random_length():
    return int(np.random.beta(2, 5) * 300)

@ell.simple(model="gpt-4o-mini")
def joke(topic : str):
    """You are a funny comedian. You respond in scripts for a standup comedy skit."""
    return f"Act out a full joke. Make your script {get_random_length()} words long. Here's the premise: {come_up_with_a_premise_for_a_joke_about(topic)}"


if __name__ == "__main__":
    ell.init(verbose=True, store='./logdir', autocommit=False)
    # Todo: Figure configuration for automcommititng.
    joke("minecraft") # <The joke>