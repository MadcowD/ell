# what happemns duiring losure
CODE_INSTURCTIONS = """

Other Instructoons:
- You only respond in code with no commentary (except in the and docstrings.) 
- Do not respond in markdown just write code. 
- It is extremely important that you don't start you code with ```python. """

class Test:
    def to_str(self):
        return f"a: {self.a}, b: {self.b}"


test = # [Test object]

import ell.caching
@ell.text("gpt-4-turbo", temperature=0.1, max_tokens=5)
def write_a_complete_python_class(user_spec : str):
    return [ell.system(f"""You are an expert python programmer capable of interpreting a user's spec and writing a python class to accomidate their request. You should document all your code, and you best practices.
    {CODE_INSTURCTIONS} {test.to_str()}
    """), ell.user(user_spec)]



# what happens during invocation
write_a_complete_python_class("lol") ->
   # Inovation(
        args = (lol,),
        kwargs = {}
        globals = {
            # attempt to serialize this.
             test: str(test)
        }
        freevars = {}
        )
