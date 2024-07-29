from functools import lru_cache
import ell
from ell.stores.sql import SQLiteStore


@ell.lm("gpt-4-turbo", temperature=0.1)
def write_a_complete_python_class(user_spec : str):
    """You are an expert python programmer capable of interpreting a user's spec and writing a python class to accomidate their request. You should document all your code, and you best practices.
    """
    return "Write a python class to accomidate the user's spec:\n" + user_spec


@ell.lm("gpt-4o-mini", temperature=0.1)
def write_one_unit_test_for_class(class_def : str):
    """You are an expert python unit test programmer."""
    return "Write a single unit test for the following class definition:\n" + class_def





if __name__ == "__main__":
    ell.config.verbose = True

    # If I'm using ell without a store then I don't 
    with ell.get_store().cache(write_a_complete_python_class):
        cls_Def = write_a_complete_python_class("A class that represents a bank")
    unit_test = write_one_unit_test_for_class(cls_Def)
    