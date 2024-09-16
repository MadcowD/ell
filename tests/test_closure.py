from functools import wraps
import random
import pytest
import math
from typing import Set, Any
import numpy as np
from ell.util.closure import (
    lexical_closure,
)
import ell
from ell.util.closure_util import get_referenced_names, should_import
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
# tests/test_closure.py

import pytest
from ell.util.closure import lexically_closured_source

# def test_lexical_closure_eliminates_redundant_dependencies():
#     # Define a shared dependency function
#     def dependency_func():
#         return "I am a shared dependency"
    
#     # Define two functions that both depend on dependency_func
#     def func_a():
#         return dependency_func()
    
#     def func_b():
#         return dependency_func()
    
#     # Define a top-level function that depends on func_a and func_b
#     def func_c():
#         return func_a() + func_b()
    
#     # Generate the lexically closured source for func_c
#     x = lexically_closured_source(func_c)
#     closure_source = x[0]
    
#     # Debugging output (optional)
#     print("Closure Source:\n", closure_source)
    
#     # Assertions to ensure each function definition appears only once
#     assert "def func_c():" in closure_source, "func_c definition should be in the closure source"
#     assert "def func_a():" in closure_source, "func_a definition should be in the closure source"
#     assert "def func_b():" in closure_source, "func_b definition should be in the closure source"
#     assert "def dependency_func():" in closure_source, "dependency_func definition should be in the closure source"
    
#     # Count the number of times each function is defined in the closure source
#     func_c_definitions = closure_source.count("def func_c():")
#     func_a_definitions = closure_source.count("def func_a():")
#     func_b_definitions = closure_source.count("def func_b():")
#     dependency_func_definitions = closure_source.count("def dependency_func():")
    
#     # Assert that each function is defined only once
#     assert func_c_definitions == 1, "func_c should be defined exactly once in the closure source"
#     assert func_a_definitions == 1, "func_a should be defined exactly once in the closure source"
#     assert func_b_definitions == 1, "func_b should be defined exactly once in the closure source"
#     assert dependency_func_definitions == 1, "dependency_func should be defined exactly once in the closure source"
    
#     # Additionally, ensure that there are no duplicate imports or dependencies
#     # (Assuming no imports are needed in this simple example)
#     # If imports exist, similar counts can be performed

#     # Optionally, verify that the closure source contains no duplicate lines
#     lines = closure_source.split("\n")
#     unique_lines = set()
#     for line in lines:
#         stripped_line = line.strip()
#         if stripped_line:  # Ignore empty lines
#             assert stripped_line not in unique_lines, f"Duplicate line found in closure source: {stripped_line}"
#             unique_lines.add(stripped_line)


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

# def test_ell_uses_only_include_ell_decorated_functions():
#     # Define an ell-decorated function
#     @ell.simple(model="gpt-4o-mini")
#     def do_nothing():
#         pass

#     # Define non-ell functions
#     def get_random_adjective():
#         adjectives = ["enthusiastic", "cheerful", "warm", "friendly", "heartfelt", "sincere"]
#         do_nothing()  # This is an ell-decorated function
#         return random.choice(adjectives)

#     def get_random_punctuation():
#         return random.choice(["!", "!!", "!!!"])

#     # Define an ell-decorated function that uses both ell and non-ell functions
#     @ell.simple(model="gpt-4o-mini")
#     def hello(name: str):
#         adjective = get_random_adjective()
#         punctuation = get_random_punctuation()
#         return f"Say a {adjective} hello to {name}{punctuation}"

#     # Generate the lexically closured source for hello
#     closure_source, (formatted_source, cleaned_source), uses = lexically_closured_source(hello)

#     # Debugging output (optional)
#     print("Closure Source:\n", closure_source)

#     # Assertions to ensure each function definition appears only once
#     assert "def hello(name: str):" in closure_source, "hello definition should be in the closure source"
#     assert "def get_random_adjective():" in closure_source, "get_random_adjective definition should be in the closure source"
#     assert "def get_random_punctuation():" in closure_source, "get_random_punctuation definition should be in the closure source"
#     assert "def do_nothing():" in closure_source, "do_nothing definition should be in the closure source"

#     # Count the number of times each function is defined in the closure source
#     hello_definitions = closure_source.count("def hello(name: str):")
#     get_random_adjective_definitions = closure_source.count("def get_random_adjective():")
#     get_random_punctuation_definitions = closure_source.count("def get_random_punctuation():")
#     do_nothing_definitions = closure_source.count("def do_nothing():")

#     # Assert that each function is defined only once
#     assert hello_definitions == 1, "hello should be defined exactly once in the closure source"
#     assert get_random_adjective_definitions == 1, "get_random_adjective should be defined exactly once in the closure source"
#     assert get_random_punctuation_definitions == 1, "get_random_punctuation should be defined exactly once in the closure source"
#     assert do_nothing_definitions == 1, "do_nothing should be defined exactly once in the closure source"

#     # Ensure that __ell_uses__ contains only ell-decorated functions
#     # Retrieve the closure attributes from the original function
#     closure_attributes = hello.__ell_closure__
#     uses_set = hello.__ell_uses__

#     # Assert that uses_set contains only do_nothing
#     assert len(uses_set) == 1, "__ell_uses__ should contain exactly one function"
#     assert do_nothing in uses_set, "__ell_uses__ should contain only do_nothing"

#     # Additionally, ensure that non-ell functions are not in __ell_uses__
#     assert get_random_adjective not in uses_set, "get_random_adjective should not be in __ell_uses__"
#     assert get_random_punctuation not in uses_set, "get_random_punctuation should not be in __ell_uses__"

#     # Ensure that dependencies include non-ell functions
#     # For simplicity, we'll check that get_random_punctuation is present as a dependency
#     assert "def get_random_punctuation():" in closure_source, "get_random_punctuation should be included as a dependency"

#     # Ensure that imports are correctly handled (e.g., random)
#     assert "import random" in closure_source, "random should be imported in the closure source"

#     # Ensure no duplicate lines exist
#     lines = closure_source.split("\n")
#     unique_lines = set()
#     for line in lines:
#         stripped_line = line.strip()
#         if stripped_line:  # Ignore empty lines
#             assert stripped_line not in unique_lines, f"Duplicate line found in closure source: {stripped_line}"
#             unique_lines.add(stripped_line)

if __name__ == "__main__":
    test_lexical_closure_uses()