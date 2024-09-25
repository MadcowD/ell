import ell
from ell.stores.sql import SQLiteStore


BASE_PROMPT = """You are an adept python programmer. Only answer in python code. Avoid markdown formatting at all costs."""

@ell.simple(model="gpt-4o", temperature=0.7, max_tokens=4)
def create_a_python_class(user_spec : str):
    return [
        ell.system(
            f"{BASE_PROMPT}\n\nYour goal to make a python class for a user based a user spec."
        ),
        ell.user(
            f"Here is the user spec: {user_spec}"
        )
    ]

@ell.simple(model="gpt-4o", temperature=0.7)
def write_unit_for_a_class(class_def : str):
    return [
        ell.system(
            f"{BASE_PROMPT}\n\nYour goal is to write only a single unit test for a specific class definition. Don't use `unittest` package"
        ),
        ell.user(
            f"Here is the class definition: {class_def}"
        )
    ]


if __name__ == "__main__":
    ell.init(store='./logdir', autocommit=True, verbose=True)

    with ell.get_store().freeze(create_a_python_class):
        _class_def = create_a_python_class("A class that represents a bank")
        _unit_tests = write_unit_for_a_class(_class_def)