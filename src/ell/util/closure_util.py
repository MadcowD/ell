import ast
import importlib
import os
import black
from dill.detect import nestedglobals

import inspect

import inspect

#!/usr/bin/env python
#
# Author: Mike McKerns (mmckerns @caltech and @uqfoundation)
# Modified by: William Guss.
# Copyright (c) 2008-2016 California Institute of Technology.
# Copyright (c) 2016-2024 The Uncertainty Quantification Foundation.
# License: 3-clause BSD.  The full license text is available at:
#  - https://github.com/uqfoundation/dill/blob/master/LICENSE

# XXX: This is a mess. COuld probably be about 100 lines of code max.
def globalvars(func, recurse=True, builtin=False):
    """get objects defined in global scope that are referred to by func

    return a dict of {name:object}"""
    while hasattr(func, "__ell_func__"):
        func = func.__ell_func__
    if inspect.ismethod(func): func = func.__func__
    while hasattr(func, "__ell_func__"):
        func = func.__ell_func__
    if inspect.isfunction(func):
        globs = vars(inspect.getmodule(sum)).copy() if builtin else {}
        # get references from within closure
        orig_func, func = func, set()
        for obj in orig_func.__closure__ or {}:
            try:
                cell_contents = obj.cell_contents
            except ValueError: # cell is empty
                pass
            else:
                _vars = globalvars(cell_contents, recurse, builtin) or {}
                func.update(_vars) #XXX: (above) be wary of infinte recursion?
                globs.update(_vars)
        # get globals
        globs.update(orig_func.__globals__ or {})
        # get names of references
        if not recurse:
            func.update(orig_func.__code__.co_names)
        else:
            func.update(nestedglobals(orig_func.__code__))
            # find globals for all entries of func
            for key in func.copy(): #XXX: unnecessary...?
                nested_func = globs.get(key)
                if nested_func is orig_func:
                   #func.remove(key) if key in func else None
                    continue  #XXX: globalvars(func, False)?
                func.update(globalvars(nested_func, True, builtin))
    elif inspect.iscode(func):
        globs = vars(inspect.getmodule(sum)).copy() if builtin else {}
       #globs.update(globals())
        if not recurse:
            func = func.co_names # get names
        else:
            orig_func = func.co_name # to stop infinite recursion
            func = set(nestedglobals(func))
            # find globals for all entries of func
            for key in func.copy(): #XXX: unnecessary...?
                if key is orig_func:
                   #func.remove(key) if key in func else None
                    continue  #XXX: globalvars(func, False)?
                nested_func = globs.get(key)
                func.update(globalvars(nested_func, True, builtin))
    else:
        return {}
    #NOTE: if name not in __globals__, then we skip it...
    return dict((name,globs[name]) for name in func if name in globs)


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


def should_import(module_name : str):
    """
    This function checks if a module should be imported based on its origin.
    It returns False if the module is in the local directory or if the module's spec is None.
    Otherwise, it returns True.

    Returns:
    bool: True if the module should be imported, False otherwise.
    """

    # Define the local directory
    DIRECTORY_TO_WATCH = os.environ.get("DIRECTORY_TO_WATCH", os.getcwd())

    # Get the module's spec
    spec = importlib.util.find_spec(module_name)

    if module_name.startswith("ell"):
        return True

    # Return False if the spec is None or if the spec's origin starts with the local directory
    if spec is None or (spec.origin is not None and spec.origin.startswith(DIRECTORY_TO_WATCH)):
        return False

    # Otherwise, return True
    return True


def format_source(source: str) -> str:
    """Format the source code using Black."""
    try:
        return black.format_str(source, mode=black.Mode())
    except:
        # If Black formatting fails, return the original source
        return source