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
from typing import Any, Dict, Set, Tuple, Callable
import dill
import inspect
import types
from dill.source import getsource
import importlib.util
import re
from collections import deque
import black

DELIM = "$$$$$$$$$$$$$$$$$$$$$$$$$"
FORBIDDEN_NAMES = ["ell", "lstr"]

def lexical_closure(
    func: Any,
    already_closed: Set[int] = None,
    initial_call: bool = False,
    recursion_stack: list = None
) -> Tuple[str, Tuple[str, str], Set[str]]:
    """
    Generate a lexical closure for a given function or callable.

    Args:
        func: The function or callable to process.
        already_closed: Set of already processed function hashes.
        initial_call: Whether this is the initial call to the function.
        recursion_stack: Stack to keep track of the recursion path.

    Returns:
        A tuple containing:
        - The full source code of the closure
        - A tuple of (function source, dependencies source)
        - A set of function hashes that this closure uses
    """
    already_closed = already_closed or set()
    uses = set()
    recursion_stack = recursion_stack or []

    if hash(func) in already_closed:
        return "", ("", ""), set()

    recursion_stack.append(getattr(func, '__qualname__', str(func)))

    outer_ell_func = func
    while hasattr(func, "__ell_func__"):
        func = func.__ell_func__

    source = getsource(func, lstrip=True)
    already_closed.add(hash(func))

    globals_and_frees = _get_globals_and_frees(func)
    dependencies, imports, modules = _process_dependencies(func, globals_and_frees, already_closed, recursion_stack, uses)
    
    cur_src = _build_initial_source(imports, dependencies, source)
    
    module_src = _process_modules(modules, cur_src, already_closed, recursion_stack, uses)
    
    dirty_src = _build_final_source(imports, module_src, dependencies, source)
    dirty_src_without_func = _build_final_source(imports, module_src, dependencies, "")

    CLOSURE_SOURCE[hash(func)] = dirty_src 

    dsrc = _clean_src(dirty_src_without_func)

    # Format the sorce and dsrc soruce using Black
    source = _format_source(source)
    dsrc = _format_source(dsrc)

    fn_hash = _generate_function_hash(source, dsrc, func.__qualname__)
    
    _update_ell_func(outer_ell_func, source, dsrc, globals_and_frees['globals'], globals_and_frees['frees'], fn_hash, uses)
    
    return (dirty_src, (source, dsrc), ({fn_hash} if not initial_call and hasattr(outer_ell_func, "__ell_func__") else uses))


def _format_source(source: str) -> str:
    """Format the source code using Black."""
    try:
        return black.format_str(source, mode=black.Mode())
    except:
        # If Black formatting fails, return the original source
        return source

def _get_globals_and_frees(func: Callable) -> Dict[str, Dict]:
    """Get global and free variables for a function."""
    globals_dict = collections.OrderedDict(globalvars(func))
    frees_dict = collections.OrderedDict(dill.detect.freevars(func))
    
    if isinstance(func, type):
        for name, method in collections.OrderedDict(func.__dict__).items():
            if isinstance(method, (types.FunctionType, types.MethodType)):
                globals_dict.update(collections.OrderedDict(dill.detect.globalvars(method)))
                frees_dict.update(collections.OrderedDict(dill.detect.freevars(method)))
    
    return {'globals': globals_dict, 'frees': frees_dict}

def _process_dependencies(func, globals_and_frees, already_closed, recursion_stack, uses):
    """Process function dependencies."""
    dependencies = []
    modules = deque()
    imports = []

    if isinstance(func, (types.FunctionType, types.MethodType)):
        _process_default_kwargs(func, dependencies, already_closed, recursion_stack, uses)

    for var_name, var_value in {**globals_and_frees['globals'], **globals_and_frees['frees']}.items():
        _process_variable(var_name, var_value, dependencies, modules, imports, already_closed, recursion_stack, uses)

    return dependencies, imports, modules

def _process_default_kwargs(func, dependencies, already_closed, recursion_stack, uses):
    """Process default keyword arguments of a function."""
    ps = inspect.signature(func).parameters
    default_kwargs = collections.OrderedDict({k: v.default for k, v in ps.items() if v.default is not inspect.Parameter.empty})
    for name, val in default_kwargs.items():
        try:
            is_builtin = val.__class__.__module__ == "builtins" or val.__class__.__module__ == "__builtins__"
        except:
            is_builtin = False
        if name not in FORBIDDEN_NAMES and not is_builtin:
            try:
                dep, _, _uses = lexical_closure(type(val), already_closed=already_closed, recursion_stack=recursion_stack.copy())
                dependencies.append(dep)
                uses.update(_uses)
            except Exception as e:
                _raise_error(f"Failed to capture the lexical closure of default parameter {name}", e, recursion_stack)

def _process_variable(var_name, var_value, dependencies, modules, imports, already_closed, recursion_stack , uses):
    """Process a single variable."""
    if isinstance(var_value, (types.FunctionType, type, types.MethodType)):
        _process_callable(var_name, var_value, dependencies, already_closed, recursion_stack, uses)
    elif isinstance(var_value, types.ModuleType):
        _process_module(var_name, var_value, modules, imports, uses)
    elif isinstance(var_value, types.BuiltinFunctionType):
        imports.append(dill.source.getimport(var_value, alias=var_name))
    else:
        _process_other_variable(var_name, var_value, dependencies, uses)

def _process_callable(var_name, var_value, dependencies, already_closed, recursion_stack, uses):
    """Process a callable (function, method, or class)."""
    try: 
        module_is_ell = 'ell' in inspect.getmodule(var_value).__name__
    except:
        module_is_ell = False

    if var_name not in FORBIDDEN_NAMES and not module_is_ell:
        try:
            dep, _, _uses = lexical_closure(var_value, already_closed=already_closed, recursion_stack=recursion_stack.copy())
            dependencies.append(dep)
            uses.update(_uses)
        except Exception as e:
            _raise_error(f"Failed to capture the lexical closure of global or free variable {var_name}", e, recursion_stack)

def _process_module(var_name, var_value, modules, imports, uses):
    """Process a module."""
    if should_import(var_value):
        imports.append(dill.source.getimport(var_value, alias=var_name))
    else:
        modules.append((var_name, var_value))

def _process_other_variable(var_name, var_value, dependencies, uses):
    """Process variables that are not callables or modules."""
    if isinstance(var_value, str) and '\n' in var_value:
        dependencies.append(f"{var_name} = '''{var_value}'''")
    elif is_immutable_variable(var_value):
        dependencies.append(f"#<BV>\n{var_name} = {repr(var_value)}\n#</BV>")
    else:
        dependencies.append(f"#<BmV>\n{var_name} = <{type(var_value).__name__} object>\n#</BmV>")

def _build_initial_source(imports, dependencies, source):
    """Build the initial source code."""
    return f"{DELIM}\n" + f"\n{DELIM}\n".join(imports + dependencies + [source]) + f"\n{DELIM}\n"

def _process_modules(modules, cur_src, already_closed, recursion_stack, uses):
    """Process module dependencies."""
    reverse_module_src = deque()
    while modules:
        mname, mval = modules.popleft()
        mdeps = []
        attrs_to_extract = get_referenced_names(cur_src.replace(DELIM, ""), mname)
        for attr in attrs_to_extract:
            _process_module_attribute(mname, mval, attr, mdeps, modules, already_closed, recursion_stack, uses)
        
        mdeps.insert(0, f"# Extracted from module: {mname}")
        reverse_module_src.appendleft("\n".join(mdeps))
        
        cur_src = _dereference_module_names(cur_src, mname, attrs_to_extract)
    
    return list(reverse_module_src)

def _process_module_attribute(mname, mval, attr, mdeps, modules, already_closed, recursion_stack, uses):
    """Process a single attribute of a module."""
    val = getattr(mval, attr)
    if isinstance(val, (types.FunctionType, type, types.MethodType)):
        try:
            dep, _, dep_uses = lexical_closure(val, already_closed=already_closed, recursion_stack=recursion_stack.copy())
            mdeps.append(dep)
            uses.update(dep_uses)
        except Exception as e:
            _raise_error(f"Failed to capture the lexical closure of {mname}.{attr}", e, recursion_stack)
    elif isinstance(val, types.ModuleType):
        modules.append((attr, val))
    else:
        mdeps.append(f"{attr} = {repr(val)}")

def _dereference_module_names(cur_src, mname, attrs_to_extract):
    """Dereference module names in the source code."""
    for attr in attrs_to_extract:
        cur_src = cur_src.replace(f"{mname}.{attr}", attr)
    return cur_src

def _build_final_source(imports, module_src, dependencies, source):
    """Build the final source code."""
    seperated_dependencies = sorted(imports) + sorted(module_src) + sorted(dependencies) + ([source] if source else [])
    seperated_dependencies = list(dict.fromkeys(seperated_dependencies))
    return DELIM + "\n" + f"\n{DELIM}\n".join(seperated_dependencies) + "\n" + DELIM + "\n"

def _generate_function_hash(source, dsrc, qualname):
    """Generate a hash for the function."""
    return "lmp-" + hashlib.md5("\n".join((source, dsrc, qualname)).encode()).hexdigest()

def _update_ell_func(outer_ell_func, source, dsrc, globals_dict, frees_dict, fn_hash, uses):
    """Update the ell function attributes."""
    if hasattr(outer_ell_func, "__ell_func__"):
        outer_ell_func.__ell_closure__ = (source, dsrc, globals_dict, frees_dict)
        outer_ell_func.__ell_hash__ = fn_hash
        outer_ell_func.__ell_uses__ = uses

def _raise_error(message, exception, recursion_stack):
    """Raise an error with detailed information."""
    error_msg = f"{message}. Error: {str(exception)}\n"
    error_msg += f"Recursion stack: {' -> '.join(recursion_stack)}"
    raise Exception(error_msg)

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

def lexically_closured_source(func):
    _, fnclosure, uses = lexical_closure(func, initial_call=True, recursion_stack=[])
    source, dsrc = fnclosure
    formatted_source = _format_source(source)
    formatted_dsrc = _format_source(dsrc)
    return (formatted_source, formatted_dsrc,) + func.__ell_closure__[2:], uses

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

#!/usr/bin/env python
#
# Author: Mike McKerns (mmckerns @caltech and @uqfoundation)
# Modified by: William Guss.
# Copyright (c) 2008-2016 California Institute of Technology.
# Copyright (c) 2016-2024 The Uncertainty Quantification Foundation.
# License: 3-clause BSD.  The full license text is available at:
#  - https://github.com/uqfoundation/dill/blob/master/LICENSE
from dill.detect import nestedglobals
import inspect

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

