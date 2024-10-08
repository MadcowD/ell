import ell2a
import numpy as np

from ell2a.stores.sql import PostgresStore

class MyPrompt:
    x : int

def get_random_length():
    return int(np.random.beta(2, 6) * 1500)

@ell2a.simple(model="gpt-4o-mini")
def hello(world : str):
    """Your goal is to be really mean to the other guy while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"


if __name__ == "__main__":
    ell2a.init(verbose=True, store=PostgresStore('postgresql://postgres:postgres@localhost:5432/ell2a'), autocommit=True)

    greeting = hello("sam altman") # > "hello sama! ... "
