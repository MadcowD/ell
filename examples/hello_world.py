import ell
import math

from ell.stores.sql import SQLiteStore
import numpy as np

ell.config.verbose = True

def get_random_length():
    return int(np.random.beta(2, 5) * 1000)

@ell.lm(model="gpt-4o-mini")
def hello(world : str):
    """You are helpful assistant""" # System prpmpt

    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name*2} characters or less!" # User prompt


# Goodbye
@ell.lm(model="gpt-4o-mini")
def goodbye(name : str, greeting : str):
    """You are helpful assistant""" # System prpmpt

    return f"Say goodbye to {name}! (Fyi: this how you greeted them)" # User prompt

if __name__ == "__main__":

    store = SQLiteStore('sqlite_example')
    store.install(autocommit=True)
    x = hello("Derick Walker") # > "hello sama!"
    
    good_bye = goodbye("Derick Walker", x)
    



