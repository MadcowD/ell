from functools import lru_cache
import ell
import ell.caching
from ell.stores.sql import SQLiteStore

CODE_INSTURCTIONS = """

Other Instructions:
- You only respond in code with no commentary (except in the and docstrings.) 
- Do not respond in markdown just write code. 
- It is extremely important that you don't start you code with ```python. """

test = ["asd"]*10

def get_lmp():
    z = 6
    @ell.lm("gpt-4o", temperature=0.1, max_tokens=6)
    def write_a_complete_python_class(user_spec : str):
        return [ell.system(f"""You are an mid-tier python programmer capable of interpreting a user's spec and writing a python class to accomidate their request. You should document all your code, and you best practices.
        {CODE_INSTURCTIONS} {z} {test[0]}
        """), ell.user(user_spec)]

    return write_a_complete_python_class

if __name__ == "__main__":
    ell.config.verbose = True
    ell.set_store(SQLiteStore("sqlite_example"), autocommit=True)
    test[0] = "modified at execution :O"
    w = get_lmp()
    cls_Def = w("A class that represents a bank")