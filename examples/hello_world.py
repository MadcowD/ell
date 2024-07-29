import ell
import numpy as np

from ell.stores.sql import SQLiteStore


def get_random_length():
    return int(np.random.beta(2, 6) * 3000)

@ell.lm(model="gpt-4o-mini")
def hello(world : str):
    """Your goal is to charm the other guy""" # System prpmpt

    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name*2} characters or more!" # User prompt


if __name__ == "__main__":
    ell.config.verbose = True
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    greeting = hello("sam altman") # > "hello sama! ... "

