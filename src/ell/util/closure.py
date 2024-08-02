"""
This should do the following.
# prompt_consts.py
import math
def test():
    return math.sin(10)

# lol3.py
import prompt_consts

X = 7
def xD():
    print(X)
    return prompt_consts.test()

###
Our goal is to use AST & dill to get a full lexical closured source of xD, with the exception of modules that are stored in site-packages. For example.

lexical_extration(xD) returns
#closure.py
import math
def test():
    return math.sin(10)

X = 7 
def xD():
    print(X)
    return test()

"""
import collections
import ast
import hashlib
import json
import os
from typing import Any, Dict, Set, Tuple
import dill
import inspect
import types
from dill.source import getsource

import importlib.util

import ast

from collections import deque
import inspect

import dill.source
import re

DELIM = "$$$$$$$$$$$$$$$$$$$$$$$$$"
SEPERATOR = "#------------------------"
FORBIDDEN_NAMES = ["ell", "lstr"]
def is_immutable_variable(value):
    """
    Check if a value is immutable.
    
    This function determines whether the given value is of an immutable type in Python.
    Immutable types are objects whose state cannot be modified after they are created.
    
    Args:
        value: Any Python object to check for immutability.
    
    Returns:
        bool: True if the value is immutable, False otherwise.
    
    Note:
        - This function checks for common immutable types in Python.
        - Custom classes are considered mutable unless they explicitly implement
          immutability (which this function doesn't check for).
        - For some types like tuple, immutability is shallow (i.e., the tuple itself
          is immutable, but its contents might not be).
    """
    immutable_types = (
        int, float, complex, str, bytes,
        tuple, frozenset, type(None),
        bool,  # booleans are immutable
        range,  # range objects are immutable
        slice,  # slice objects are immutable
    )
    
    if isinstance(value, immutable_types):
        return True
    
    # Check for immutable instances of mutable types
    if isinstance(value, (tuple, frozenset)):
        return all(is_immutable_variable(item) for item in value)
    
    return False


def should_import(module: types.ModuleType):
    """
    This function checks if a module should be imported based on its origin.
    It returns False if the module is in the local directory or if the module's spec is None.
    Otherwise, it returns True.

    Parameters:
    module (ModuleType): The module to check.

    Returns:
    bool: True if the module should be imported, False otherwise.
    """
    # Define the local directory
    DIRECTORY_TO_WATCH = os.environ.get("DIRECTORY_TO_WATCH", os.getcwd())

    # Get the module's spec
    spec = importlib.util.find_spec(module.__name__)

    if module.__name__.startswith("ell"):
        return True
    
    # Return False if the spec is None or if the spec's origin starts with the local directory
    if spec is None or (spec.origin is not None and spec.origin.startswith(DIRECTORY_TO_WATCH)):
        return False

    # Otherwise, return True
    return True


import ast


def get_referenced_names(code: str, module_name: str):
    """
    This function takes a block of code and a module name as input. It parses the code into an Abstract Syntax Tree (AST)
    and walks through the tree to find all instances where an attribute of the module is referenced in the code.

    Parameters:
    code (str): The block of code to be parsed.
    module_name (str): The name of the module to look for in the code.

    Returns:
    list: A list of all attributes of the module that are referenced in the code.
    """
    tree = ast.parse(code)
    referenced_names = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == module_name:
                referenced_names.append(node.attr)

    return referenced_names


CLOSURE_SOURCE: Dict[str, str] = {}


def lexical_closure(func: Any, already_closed=None, initial_call=False, recursion_stack=None) -> Tuple[str, Tuple[str, str], Set[str]]:
    """
    This function takes a function or any callable as input and returns a string representation of its lexical closure.
    The lexical closure includes the source code of the function itself, as well as the source code of any global variables,
    free variables, and dependencies (other functions or classes) that it references.

    If the input function is a method of a class, this function will also find and include the source code of other methods
    in the same class that are referenced by the input function.

    The resulting string can be used to recreate the function in a different context, with all of its dependencies.

    Parameters:
    func (Callable): The function or callable whose lexical closure is to be found.
    already_closed (set): Set of already processed functions to avoid infinite recursion.
    initial_call (bool): Whether this is the initial call to the function.
    recursion_stack (list): Stack to keep track of the recursion path.

    Returns:
    str: A string representation of the lexical closure of the input function.
    """

    already_closed = already_closed or set()
    uses = set()
    recursion_stack = recursion_stack or []

    if hash(func) in already_closed:
        return "", ("", ""), {}

    recursion_stack.append(func.__qualname__ if hasattr(func, '__qualname__') else str(func))

    outer_ell_func = func
    while hasattr(func, "__ell_func__"):
        func = func.__ell_func__
    
    source = getsource(func, lstrip=True)
    already_closed.add(hash(func))
    # if func is nested func
    # Parse the source code into an AST
    # tree = ast.parse(source)
    # Find all the global variables and free variables in the function

    # These are not global variables these are globals, and other shit is actualy in cluded here
    _globals = collections.OrderedDict(dill.detect.globalvars(func))
    print(_globals)
    _frees = collections.OrderedDict(dill.detect.freevars(func))

    # If func is a class we actually should check all the methods of the class for globalvars. Malekdiction (MSM) was here.
    # Add the default aprameter tpes to depndencies if they are not builtins

    if isinstance(func, type):
        # Now we need to get all the global vars in the class
        for name, method in collections.OrderedDict(func.__dict__).items():
            if isinstance(method, types.FunctionType) or isinstance(
                method, types.MethodType
            ):
                _globals.update(
                    collections.OrderedDict(dill.detect.globalvars(method))
                )
                _frees.update(collections.OrderedDict(dill.detect.freevars(method)))

    # Initialize a list to store the source code of the dependencies
    dependencies = []
    modules = deque()
    imports = []

    if isinstance(func, (types.FunctionType, types.MethodType)):
        # Get all the the default kwargs
        ps = inspect.signature(func).parameters
        default_kwargs = collections.OrderedDict(
            {
                k: v.default
                for k, v in ps.items()
                if v.default is not inspect.Parameter.empty
            }
        )
        for name, val in default_kwargs.items():
            try:
                if name not in FORBIDDEN_NAMES:
                    dep, _,  dep_uses = lexical_closure(
                        type(val), already_closed=already_closed,
                        recursion_stack=recursion_stack.copy()
                    )
                    dependencies.append(dep)
                    uses.update(dep_uses)

            except Exception as e:
                error_msg = f"Failed to capture the lexical closure of default parameter {name}. Error: {str(e)}\n"
                error_msg += f"Recursion stack: {' -> '.join(recursion_stack)}"
                raise Exception(error_msg)

    # Iterate over the global variables
    for var_name, var_value in {**_globals, **_frees}.items():
        is_free = var_name in _frees
        # If the variable is a function, get its source code
        if isinstance(var_value, (types.FunctionType, type, types.MethodType)):
            if var_name not in FORBIDDEN_NAMES:
                try:
                    ret = lexical_closure(
                        var_value, already_closed=already_closed,
                        recursion_stack=recursion_stack.copy()
                    )
                    dep, _, dep_uses = ret
                    dependencies.append(dep)
                    # See if the function was called at all in the source code of the func
                    # This is wrong because if its a referred call it won't track the dependency; so we actually need to trace all dependencies that are not ell funcs to see if they call it as well.
                    if is_function_called(var_name, source):
                        uses.update(dep_uses)
                except Exception as e:
                    error_msg = f"Failed to capture the lexical closure of global or free variabl evariable {var_name}. Error: {str(e)}\n"
                    error_msg += f"Recursion stack: {' -> '.join(recursion_stack)}"
                    raise Exception(error_msg)

        elif isinstance(var_value, types.ModuleType):
            if should_import(var_value):
                imports += [dill.source.getimport(var_value, alias=var_name)]

            else:
                # Now we need to find all the variables in this module that were referenced
                modules.append((var_name, var_value))
        elif isinstance(var_value, types.BuiltinFunctionType):
            # we need to get an import for it

            imports += [dill.source.getimport(var_value, alias=var_name)]

        else:
            json_default = lambda x: f"<Object of type {type(x).__name__}>"
            if isinstance(var_value, str) and '\n' in var_value:
                dependencies.append(f"{var_name} = '''{var_value}'''")
            else:
                # if is immutable
                if is_immutable_variable(var_value) and not is_free:
                    dependencies.append(f"#<BV>\n{var_name} = {repr(var_value)}\n#</BV>")
                else:

                    dependencies.append(f"#<BmV>\n{var_name} = <{type(var_value).__name__} object>\n#</BmV>")

    # We probably need to resovle things with topological sort & turn stuff into a dag but for now we can just do this

    cur_src = (
        DELIM
        + "\n"
        + f"\n{DELIM}\n".join(imports + dependencies)
        + "\n"
        + DELIM
        + "\n"
        + source
        + "\n"
        + DELIM
        + "\n"
    )

    reverse_module_src = deque()
    while len(modules) > 0:
        mname, mval = modules.popleft()
        mdeps = []
        attrs_to_extract = get_referenced_names(cur_src.replace(DELIM, ""), mname)
        for attr in attrs_to_extract:
            val = getattr(mval, attr)
            if isinstance(val, (types.FunctionType, type, types.MethodType)):
                try:
                    dep, _, dep_uses = lexical_closure(
                        val, already_closed=already_closed,
                        recursion_stack=recursion_stack.copy()
                    )
                    mdeps.append(dep)
                    uses.update(dep_uses)
                except Exception as e:
                    error_msg = f"Failed to capture the lexical closure of {mname}.{attr}. Error: {str(e)}\n"
                    error_msg += f"Recursion stack: {' -> '.join(recursion_stack)}"
                    raise Exception(error_msg)
            elif isinstance(val, types.ModuleType):
                modules.append((attr, val))
            else:
                # If its another module we need to add it to the list of modules
                mdeps.append(f"{attr} = {repr(val)}")

        mdeps.insert(0, f"# Extracted from module: {mname}")

        # Now let's dereference all the module names in our cur_src
        for attr in attrs_to_extract:
            # Go throught hte dependencies and replace all the module names with the attr
            source = source.replace(f"{mname}.{attr}", attr)
            dependencies = [
                dep.replace(f"{mname}.{attr}", attr) for dep in dependencies
            ]
        # Now add all the module dependencies to the top of the list
        reverse_module_src.appendleft("\n".join(mdeps))

    # Now we need to add the module dependencies to the top of the source
    # Sort the dependencies
    dependencies = sorted(dependencies)
    imports = sorted(imports)
    reverse_module_src = sorted(reverse_module_src)
    seperated_dependencies = (
        imports
        + list(reverse_module_src)
        + dependencies
        + [source]
    )
    # Remove duplicates and preserve order
    seperated_dependencies = list(dict.fromkeys(seperated_dependencies))

    dirty_src = DELIM + "\n" + f"\n{DELIM}\n".join(seperated_dependencies) + "\n" + DELIM + "\n" 
    dirty_src_without_func = DELIM + "\n" + f"\n{DELIM}\n".join(seperated_dependencies[:-1]) + "\n" + DELIM + "\n"

    CLOSURE_SOURCE[hash(func)] = dirty_src 

    dsrc = _clean_src(dirty_src_without_func)
    fn_hash = "lmp-" + hashlib.md5(
            "\n".join((source, dsrc, func.__qualname__)).encode()
        ).hexdigest()
    
    if hasattr(outer_ell_func, "__ell_func__"):
        outer_ell_func.__ell_closure__ = (source, dsrc, _globals, _frees)
        outer_ell_func.__ell_hash__ = fn_hash
        outer_ell_func.__ell_uses__ = uses


    return (dirty_src, (source, dsrc), ({fn_hash}  if not initial_call and hasattr(outer_ell_func, "__ell_func__") else uses))



def lexically_closured_source(func):
    _, fnclosure, uses = lexical_closure(func, initial_call=True, recursion_stack=[])
    return fnclosure, uses

import ast

def _clean_src(dirty_src):

    # Now remove all duplicates and preserve order
    split_by_setion = filter(lambda x: len(x.strip()) > 0, dirty_src.split(DELIM))

    # Now we need to remove all the duplicates
    split_by_setion = list(dict.fromkeys(split_by_setion))

    # Now we need to concat all together
    all_imports = []
    final_src = "\n".join(split_by_setion)
    out_final_src = final_src[:]
    for line in final_src.split("\n"):
        if line.startswith("import") or line.startswith("from"):
            all_imports.append(line)
            out_final_src = out_final_src.replace(line, "")

    all_imports = "\n".join(sorted(all_imports))
    final_src = all_imports + "\n" + out_final_src

    # now replace all "\n\n\n" or longer with "\n\n"
    final_src = re.sub(r"\n{3,}", "\n\n", final_src)

    return final_src


def is_function_called(func_name, source_code):
    """
    Check if a function is called in the given source code.

    Parameters:
    func_name (str): The name of the function to check.
    source_code (str): The source code to check.

    Returns:
    bool: True if the function is called, False otherwise.
    """
    # Parse the source code into an AST
    tree = ast.parse(source_code)

    # Walk through all the nodes in the AST
    for node in ast.walk(tree):
        # If the node is a function call
        if isinstance(node, ast.Call):
            # If the function being called is the function we're looking for
            if isinstance(node.func, ast.Name) and node.func.id == func_name:
                return True

    # If we've gone through all the nodes and haven't found a call to the function, it's not called
    return False