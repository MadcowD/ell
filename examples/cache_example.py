from functools import lru_cache
import ell
import ell.caching
from ell.stores.sql import SQLiteStore

CODE_INSTURCTIONS = """

Other Instructoons:
- You only respond in code with no commentary (except in the and docstrings.) 
- Do not respond in markdown just write code. 
- It is extremely important that you don't start you code with ```python. """


class Test:
    a : int = 6
    pass
test = [Test() for _ in range(10)]


@ell.lm("gpt-4o", temperature=0.1, max_tokens=6)
def write_a_complete_python_class(user_spec : str):
    return [ell.system(f"""You are an mid-tier python programmer capable of interpreting a user's spec and writing a python class to accomidate their request. You should document all your code, and you best practices.
    {CODE_INSTURCTIONS} {test[0].a}
    """), ell.user(user_spec)]



if __name__ == "__main__":
    ell.config.verbose = True
    ell.set_store(SQLiteStore("sqlite_example"), autocommit=True)


    cls_Def = write_a_complete_python_class("A class that represents a bank")


    cls_Def = write_a_complete_python_class("A class that represents a bank")
