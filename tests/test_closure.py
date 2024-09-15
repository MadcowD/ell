from functools import wraps
import pytest
import math
from typing import Set, Any
import numpy as np
from ell.util.closure import (
    lexical_closure,
    should_import,
    get_referenced_names,
)
import ell
from ell.util.serialization import is_immutable_variable


def test_lexical_closure_simple_function():
    def simple_func(x):
        return x * 2

    result, (source, dsrc), uses = lexical_closure(simple_func)
    assert "def simple_func(x):" in result
    assert "return x * 2" in result
    assert isinstance(uses, Set)

def test_lexical_closure_with_global():
    global_var = 10
    def func_with_global():
        return global_var

    result, _, _ = lexical_closure(func_with_global)
    assert "global_var = 10" in result
    assert "def func_with_global():" in result

def test_lexical_closure_with_nested_function():
    def outer():
        def inner():
            return 42
        return inner()

    result, _, _ = lexical_closure(outer)
    assert "def outer():" in result
    assert "def inner():" in result
    assert "return 42" in result

def test_lexical_closure_with_default_args():
    def func_with_default(x=10):
        return x

    result, _, _ = lexical_closure(func_with_default)
    print(result)
    
    assert "def func_with_default(x=10):" in result

@pytest.mark.parametrize("value, expected", [
    (42, True),
    ("string", True),
    ((1, 2, 3), True),
    ([1, 2, 3], False),
    ({"a": 1}, False),
])
def test_is_immutable_variable(value, expected):
    assert is_immutable_variable(value) == expected

def test_should_import():
    import os
    assert should_import(os.__name__)
    
    class DummyModule:
        __name__ = "dummy"
    dummy = DummyModule()
    assert not should_import(dummy.__name__)

def test_get_referenced_names():
    code = """
import math
result = math.sin(x) + math.cos(y)
    """
    referenced = get_referenced_names(code, "math")
    print(referenced)
    assert "sin" in referenced
    assert "cos" in referenced

# def test_is_function_called():
#     code = """
# def foo():
#     pass

# def bar():
#     foo()

# x = 1 + 2
#     """
#     assert is_function_called("foo", code)
#     assert not is_function_called("bar", code)
#     assert not is_function_called("nonexistent", code)

# Addressing linter errors
def test_lexical_closure_signature():
    def dummy_func():
        pass

    # Test that the function accepts None for these arguments
    result, _, _ = lexical_closure(dummy_func, already_closed=None, recursion_stack=None)
    assert result  # Just check that it doesn't raise an exception

def test_lexical_closure_uses_type():
    def dummy_func():
        pass

    _, _, uses = lexical_closure(dummy_func, initial_call=True)
    assert isinstance(uses, Set)
    # You might want to add a more specific check for the content of 'uses'


def test_lexical_closure_uses():
    ell.config.lazy_versioning = False
    @ell.simple(model="gpt-4")
    def dependency_func():
        return "42"
    

    @ell.simple(model="gpt-4")
    def main_func():
        return dependency_func() 

    
    # print(main_func.__ell_uses__)
    assert isinstance(main_func.__ell_uses__, set)
    
    assert  dependency_func.__ell_hash__ in list(map(lambda x: x.__ell_hash__, main_func.__ell_uses__))
    assert len(main_func.__ell_uses__) == 1
    # Check that the item in the set starts with 'lmp-'
    assert all(hash.startswith('lmp-') for hash in map(lambda x: x.__ell_hash__, main_func.__ell_uses__))
    assert len(dependency_func.__ell_uses__) == 0
    

def test_lexical_closure_with_multiple_nested_functions():
    def outer():
        a = 1
        def middle():
            b = 2
            def inner():
                return a + b
            return inner()
        return middle()
    
    closure, (_, _), uses = lexical_closure(outer)
    assert "def outer():" in closure
    assert "def middle():" in closure
    assert "def inner():" in closure
    assert "a = 1" in closure
    assert "b = 2" in closure
    assert "return a + b" in closure
    assert isinstance(uses, Set)

def test_lexical_closure_with_class_methods():
    class MyClass:
        class_var = 10
        
        def method(self, x):
            return self.class_var + x
        
        @classmethod
        def class_method(cls, y):
            return cls.class_var + y
        
        @staticmethod
        def static_method(z):
            return z * 2
    
    closure_method, (_, _), uses_method = lexical_closure(MyClass.method)
    # assert "class MyClass" in closure_method # We don't want ot serialize the class.
    assert "def method(self, x):" in closure_method
    assert "self.class_var + x" in closure_method
    
    closure_class_method, (_, _), uses_class_method = lexical_closure(MyClass.class_method)
    assert "def class_method(cls, y):" in closure_class_method
    assert "cls.class_var + y" in closure_class_method
    
    closure_static_method, (_, _), uses_static_method = lexical_closure(MyClass.static_method)
    assert "def static_method(z):" in closure_static_method
    assert "z * 2" in closure_static_method

# def test_lexical_closure_with_recursive_function():
#     def factorial(n):
#         if n == 0:
#             return 1
#         else:
#             return n * factorial(n - 1)
    
#     closure, (_, _), uses = lexical_closure(factorial)
#     assert "def factorial(n):" in closure
#     assert "return n * factorial(n - 1)" in closure
#     assert isinstance(uses, Set)

# def test_lexical_closure_with_mutable_free_variable():
#     data = {"count": 0}
    
#     def increment():
#         data["count"] += 1
#         return data["count"]
    
#     closure, (_, _), uses = lexical_closure(increment)
#     # assert "'count': 0" in closure
#     assert "<dict object>" in closure
#     assert "def increment():" in closure
#     assert "data[\"count\"] += 1" in closure
#     assert isinstance(uses, Set)


def test_lexical_closure_with_error_in_function():
    def faulty_func():
        return undefined_variable + 1  # This will raise NameError
    
    # with pytest.raises(Exception) as exc_info:
    lexical_closure(faulty_func)
    
    # assert "Failed to capture the lexical closure" in str(exc_info.value)
    # assert "NameError" in str(exc_info.value)

def test_lexical_closure_with_multiple_decorators():
    def decorator_one(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    def decorator_two(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    @decorator_one
    @decorator_two
    def decorated_func(x):
        return x * 2
    
    closure, (_, _), uses = lexical_closure(decorated_func)
    assert "def decorated_func(x):" in closure
    assert "return x * 2" in closure
    assert isinstance(uses, Set)

def test_lexical_closure_with_class_and_imported_function():
    from math import sqrt
    
    class Helper:
        def help(self, y):
            return sqrt(y)
    
    # Todo: Currently we don't supprot type closuring. This needs to be fixed.
    helper = Helper()
    
    def compute(x):
        return helper.help(x) + sqrt(x)
    
    closure, (_, _), uses = lexical_closure(compute)
    assert "from math import sqrt" in closure
    # assert "class Helper:" in closure
    # assert "def help(self, y):" in closure
    # assert "return sqrt(y)" in closure
    assert "def compute(x):" in closure
    assert "helper.help(x) + sqrt(x)" in closure
    assert isinstance(uses, Set)

# def test_lexical_closure_with_circular_dependencies():
#     # Simulate circular dependencies by defining two functions that reference each other
#     def func_a():
#         return func_b() + 1
    
#     def func_b():
#         return func_a() + 1
    
#     closure_a, (_, _), uses_a = lexical_closure(func_a)
#     closure_b, (_, _), uses_b = lexical_closure(func_b)
    
#     assert "def func_a():" in closure_a
#     assert "return func_b() + 1" in closure_a
#     assert "def func_b():" in closure_b
#     assert "return func_a() + 1" in closure_b
#     assert isinstance(uses_a, Set)
#     assert isinstance(uses_b, Set)

def test_lexical_closure_with_import_aliases():
    import math as m
    
    def compute_circle_area(radius):
        return m.pi * radius ** 2
    
    closure, (_, _), uses = lexical_closure(compute_circle_area)
    assert "import math as m" in closure
    assert "def compute_circle_area(radius):" in closure
    assert "return m.pi * radius ** 2" in closure
    assert isinstance(uses, Set)

import asyncio

def test_lexical_closure_with_async_function():
    async def async_func(x):
        await asyncio.sleep(1)
        return x * 2
    
    closure, (_, _), uses = lexical_closure(async_func)
    assert "async def async_func(x):" in closure
    assert "await asyncio.sleep(1)" in closure
    assert "return x * 2" in closure
    assert isinstance(uses, Set)

# def test_lexical_closure_with_reexported_modules():
#     # Simulate re-exported modules
#     # module_a.py
#     import math
#     def func_a():
#         return math.sqrt(16)
    
#     # module_b.py
#     from module_a import func_a
    
#     def func_b():
#         return func_a()
    
#     closure, (_, _), uses = lexical_closure(func_b)
#     assert "from module_a import func_a" in closure
#     assert "def func_b():" in closure
#     assert "return func_a()" in closure
#     assert isinstance(uses, Set)

if __name__ == "__main__":
    test_lexical_closure_uses()