"""
An example of how to utilize the serializer to save and load invocations from the model.
"""

import ell
from ell.store import Store
from ell.stores.jsonl import FilesystemSerializer


@ell.lm(model="gpt-4-turbo",  temperature=0.1, max_tokens=5)
def some_lmp(*args, **kwargs):
    """Just a normal doc string"""
    return [
        ell.system("Test system prompt from message fmt"),
        ell.user("Test user prompt 3"),
    ]


@ell.lm(model="gpt-4-turbo",  temperature=0.1, max_tokens=5)
def some_lmp_2(output_from_some_lmp_1):
    """Just a normal doc string"""
    return [
        ell.system("Test system prompt from message fmt"),
        ell.user("Test user prompt 3"),
    ]

if __name__ == "__main__":
    serializer = FilesystemSerializer("./filesystem_serializer_example")
    serializer.install()  # Any invocation hereafter will be saved.
    
    # Example usage
    result = some_lmp()
    print(result)