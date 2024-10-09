from functools  import lru_cache
import ell2a
from ell2a.stores.sql import SQLiteStore

CODE_INSTURCTIONS = """

Other Instructions:
- You only respond in code without any commentary (except in the docstrings.) 
- Don't respond in markdown just write code!
- It is extremely important that you don't start you code with ```python <...> """

class Tests:
    pass
test = Tests()

another_serializeable_global = ["asd"]


def get_lmp(z = 10):
    y = 13
    y = z

    @ell2a.simple("gpt-4o-mini", temperature=0.1, max_tokens=6)
    def write_a_complete_python_class(user_spec : str):
        return [ell2a.system(f"""You are an mid-tier python programmer capable of interpreting a user's spec and writing a python class to accomidate their request. You should document all your code, and you best practices.
        {CODE_INSTURCTIONS} {z} {y} {test} {another_serializeable_global}
        """), ell2a.user(user_spec)]

    return write_a_complete_python_class


if __name__ == "__main__":
    ell2a.init(verbose=True, store=SQLiteStore("./logdir"), autocommit=True)
    # test[0] = "modified at execution :O"
    w = get_lmp(z=20)
    cls_Def = w("A class that represents a bank")
