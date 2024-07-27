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
FORBIDDEN_NAMES = ["ell", "Ell", "lstr"]


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

    # Return False if the spec is None or if the spec's origin starts with the local directory
    if spec is None or spec.origin.startswith(DIRECTORY_TO_WATCH):
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


def lexical_closure(func: Any, already_closed=None, initial_call=False) -> Tuple[str, Tuple[str, str], Set[str]]:
    """
    This function takes a function or any callable as input and returns a string representation of its lexical closure.
    The lexical closure includes the source code of the function itself, as well as the source code of any global variables,
    free variables, and dependencies (other functions or classes) that it references.

    If the input function is a method of a class, this function will also find and include the source code of other methods
    in the same class that are referenced by the input function.

    The resulting string can be used to recreate the function in a different context, with all of its dependencies.

    Parameters:
    func (Callable): The function or callable whose lexical closure is to be found.

    Returns:
    str: A string representation of the lexical closure of the input function.
    """

    already_closed = already_closed or set()
    uses = set()

    if hash(func) in already_closed:
        return "", ("", ""), {}


    outer_ell_func = func
    while hasattr(func, "__ell_func__"):
        func = func.__ell_func__
    
    print("Getting source for", func)
    source = getsource(func, lstrip=True)
    already_closed.add(hash(func))
    # if func is nested func
    # Parse the source code into an AST
    # tree = ast.parse(source)
    # Find all the global variables and free variables in the function
    global_vars = collections.OrderedDict(dill.detect.globalvars(func))
    free_vars = collections.OrderedDict(dill.detect.freevars(func))

    # If func is a class we actually should check all the methods of the class for globalvars. Malekdiction (MSM) was here.
    # Add the default aprameter tpes to depndencies if they are not builtins

    if isinstance(func, type):
        # Now we need to get all the global vars in the class
        for name, method in collections.OrderedDict(func.__dict__).items():
            if isinstance(method, types.FunctionType) or isinstance(
                method, types.MethodType
            ):
                global_vars.update(
                    collections.OrderedDict(dill.detect.globalvars(method))
                )
                free_vars.update(collections.OrderedDict(dill.detect.freevars(method)))

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
                    )
                    dependencies.append(dep)
                    uses.update(dep_uses)

            except (IOError, TypeError):
                # If it's a builtin we can just ignore it
                pass

    # Iterate over the global variables
    for var_name, var_value in global_vars.items():
        # If the variable is a function, get its source code
        if isinstance(var_value, (types.FunctionType, type, types.MethodType)):
            if var_name not in FORBIDDEN_NAMES:
                ret = lexical_closure(
                    var_value, already_closed=already_closed,
                )
                dep, _, dep_uses = ret
                dependencies.append(dep)
                # See if the function was called at all in the source code of the func
                # This is wrong because if its a referred call it won't track the dependency; so we actually need to trace all dependencies that are not ell funcs to see if they call it as well.
                if is_function_called(var_name, source):
                    uses.update(dep_uses)

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
            # FIXME: Doesn't work wit binary values. But does work with
            # the actual current value of a fn so if a global changes a bunch duringexecution,
            # Will have the repr value of the global at that time
            # Ideally everything is static but this is indeed fucked :);
            # That is this is nto a reserializeable representation of the prompt
            # and we cannot use this in a produciton library.
            dependencies.append(f"{var_name} = {repr(var_value)}")

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
                dep, _,  dep_uses = lexical_closure(
                    val, already_closed=already_closed
                )
                mdeps.append(dep)
                uses.update(dep_uses)
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
        outer_ell_func.__ell_closure__ = (source, dsrc)
        outer_ell_func.__ell_hash__ = fn_hash
        outer_ell_func.__ell_uses__ = uses


    return (dirty_src, (source, dsrc), ({fn_hash}  if not initial_call and hasattr(outer_ell_func, "__ell_func__") else uses))

def lexically_closured_source(func):
    _, fnclosure, uses = lexical_closure(func, initial_call=True)
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
