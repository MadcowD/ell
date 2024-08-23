import ell
import numpy as np

from ell.stores.sql import SQLiteStore


def get_random_length():
    return int(np.random.beta(2, 6) * 1500)

@ell.multimodal(model="gpt-4o-mini")
def hello(world : str):
    """Your goal is to be really meant to the other guy whiel say hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"


if __name__ == "__main__":
    ell.config.verbose = True
    ell.set_store(SQLiteStore('sqlite_example'), autocommit=True)

    greeting = hello("sam altman") # > "hello sama! ... "
    # print(greeting[0:5].__origin_trace__)



    # F_Theta: X -> Y

    # my_prompt_omega:  Z -> X


