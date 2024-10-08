
from typing import Callable

# The follwoing works...



def decorator(fn : Callable):
    def wrapper(*args, **kwargs):
        print("before")
        result = fn(*args, **kwargs)
        print("after")
        return result
    return wrapper


class TestCallable:
    def __init__(self, fn : Callable):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

def convert_to_test_callable(fn : Callable):
    return TestCallable(fn)

x = TestCallable(lambda : 1)

@decorator
@convert_to_test_callable
def test():
    print("test")

@decorator
class MyCallable:
    def __init__(self, fn : Callable):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)
    
# Oh so now ell2a.simples can actually be used as decorators on classes
