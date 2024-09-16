""""
Example originally from Instructor docs https://python.useinstructor.com/examples/knowledge_graph/
All rights reserved to the original author.
"""

from graphviz import Digraph
from pydantic import BaseModel, Field
from typing import List, Optional


class Node(BaseModel):
    id: int
    label: str
    color: str


class Edge(BaseModel):
    source: int
    target: int
    label: str
    color: str = Field(description="The color of the edge. Defaults to black.")


class KnowledgeGraph(BaseModel):
    nodes: Optional[List[Node]] = Field(..., default_factory=list)
    edges: Optional[List[Edge]] = Field(..., default_factory=list)

    def update(self, other: "KnowledgeGraph") -> "KnowledgeGraph":
        """Updates the current graph with the other graph, deduplicating nodes and edges."""
        # Create dictionaries to store unique nodes and edges
        unique_nodes = {node.id: node for node in self.nodes}
        unique_edges = {(edge.source, edge.target, edge.label): edge for edge in self.edges}

        # Update with nodes and edges from the other graph
        for node in other.nodes:
            unique_nodes[node.id] = node
        for edge in other.edges:
            unique_edges[(edge.source, edge.target, edge.label)] = edge

        return KnowledgeGraph(
            nodes=list(unique_nodes.values()),
            edges=list(unique_edges.values()),
        )

    def draw(self, prefix: str = None):
        dot = Digraph(comment="Knowledge Graph")

        for node in self.nodes:  
            dot.node(str(node.id), node.label, color=node.color)

        for edge in self.edges:  
            dot.edge(
                str(edge.source), str(edge.target), label=edge.label, color=edge.color
            )
        dot.render(prefix, format="png", view=True)


import ell

@ell.simple(model="o1-mini")
def update_knowledge_graph(cur_state: KnowledgeGraph, inp: str, i: int, num_iterations: int):
    return [
        ell.user(f"""You are a going to build a graph of how the following process works in as extreme detail as possible. Don't build a call graph. Build a graph of the actual process of lexical closure.

                You are given the current state of the graph, and you must append the nodes and edges   to it Do not procide any duplcates and try to reuse nodes as much as possible. Extract any new nodes and edges from the following:
                Here is the current state of the graph:
                {cur_state.model_dump_json(indent=2)}
                You will produce an update to the graph that that will overwtite nodes and add edges (you cannot remove them.) 
                Answer only in this JSON format:
                {KnowledgeGraph.model_json_schema()}
                Do not wrap your JSON update in back ticks (```)
                Do not include any other text.
                """),
        ell.user(f"""
        # Part {i}/{num_iterations} of the source code:

        {inp}"""),
    ]

def generate_graph(input: List[str]) -> KnowledgeGraph:
    cur_state = KnowledgeGraph()  
    num_iterations = len(input)
    for i, inp in enumerate(input):
        new_updates = update_knowledge_graph(cur_state, inp, i, num_iterations)
        # Try to parse it
        new_updates = new_updates.replace("```json", '"')
        new_updates = new_updates.replace("```", '"')
        new_updates = KnowledgeGraph.model_validate_json(new_updates)
        cur_state = cur_state.update(new_updates)  
        cur_state.draw(prefix=f"iteration_{i}")
    return cur_state

        


if __name__ == "__main__":
    ell.init(verbose=True, store='./logdir', autocommit=True)
    generate_graph(['''
        # src/ell/util/closure.py

import collections
import hashlib
import inspect
import re
import types
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set, Tuple, List

import itertools
import dill
from dill.source import getsource

from ell.util.closure_util import (
    format_source,
    get_referenced_names,
    globalvars,
    should_import,
)
from ell.util.serialization import is_immutable_variable

# Constants
FORBIDDEN_NAMES = {"ell", "lstr"}


@dataclass
class Dependency:
    """Represents a dependency with its source code."""
    source: str


@dataclass
class ModuleDependency:
    """Represents a module and its associated dependencies."""
    name: str
    value: Any
    dependencies: List[Dependency] = field(default_factory=list)


@dataclass
class Closure:
    """Aggregates all closure-related information for a function."""
    source: str
    dependencies: List[Dependency] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    modules: deque = field(default_factory=deque)
    uses: Set[Any] = field(default_factory=set)


def lexical_closure(
    func: Any,
    already_closed: Optional[Set[int]] = None,
    initial_call: bool = False,
    recursion_stack: Optional[List[str]] = None,
    forced_dependencies: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Tuple[str, str], Set[Any]]:
    """
    Generate a lexical closure for a given function or callable.

    Args:
        func: The function or callable to process.
        already_closed: Set of already processed function hashes.
        initial_call: Indicates if this is the initial call.
        recursion_stack: Tracks the recursion path.
        forced_dependencies: Additional dependencies to include.

    Returns:
        A tuple containing:
            - Full source code of the closure.
            - A tuple of (formatted source, cleaned source).
            - A set of function objects used in the closure.
    """
    already_closed = already_closed or set()
    recursion_stack = recursion_stack or []
    forced_dependencies = forced_dependencies or {}

    original_func, wrapper_func = _unwrap_function(func)

    func_hash = hash(original_func)
    if func_hash in already_closed:
        return "", ("", ""), set()

    try:
        source = getsource(original_func, lstrip=True)
    except (IOError, TypeError) as e:
        _raise_error(
            f"Unable to retrieve source for function '{original_func.__qualname__}'",
            e,
            recursion_stack,
        )

    closure = Closure(source=source)
    already_closed.add(func_hash)
    recursion_stack.append(original_func.__qualname__)

    globals_and_frees = _get_globals_and_frees(original_func)
    _process_dependencies(original_func, globals_and_frees, closure, already_closed, recursion_stack)

    for name, dependency in forced_dependencies.items():
        _process_dependency(dependency, closure, already_closed, recursion_stack, name=name)

    final_source = _assemble_final_source(closure)

    cleaned_source = _clean_source(final_source)

    formatted_source = format_source(closure.source)
    formatted_cleaned = format_source(cleaned_source)

    function_hash = _generate_function_hash(formatted_source, formatted_cleaned, original_func.__qualname__)

    # Set closure attributes on wrapper_func if exists, else on original_func
    target_func = wrapper_func if wrapper_func else original_func
    if isinstance(target_func, types.MethodType):
        target_func = target_func.__func__

    target_func.__ell_closure__ = (
        formatted_source,
        formatted_cleaned,
        globals_and_frees["globals"],
        globals_and_frees["frees"],
    )
    target_func.__ell_hash__ = function_hash
    # Only add to __ell_uses__ if it's an ell-decorated function
    if hasattr(original_func, "__ell_func__"):
        closure.uses.add(original_func)
    target_func.__ell_uses__ = {fn for fn in closure.uses if hasattr(fn, "__ell_func__")}

    uses_set = {original_func} if not initial_call else closure.uses
    return final_source, (formatted_source, cleaned_source), uses_set


def lexically_closured_source(
    func: Callable, forced_dependencies: Optional[Dict[str, Any]] = None
) -> Tuple[str, Tuple[str, str], Set[Any]]:
    """
    Generate a lexically closured source for a given function.

    This function creates a self-contained version of the provided callable,
    capturing all dependencies, including global and free variables.

    Args:
        func (Callable): The function or callable to process.
        forced_dependencies (Optional[Dict[str, Any]]): Additional dependencies
            to include in the closure.

    Returns:
        Tuple containing:
            1. The full closure source code as a string.
            2. A tuple with (formatted source, cleaned source).
            3. A set of function objects used in the closure.

    Raises:
        ValueError: If the input is not callable.
    """
    if not callable(func):
        raise ValueError("Input must be a callable object (function, method, or class).")

    closure_source, (formatted_source, cleaned_source), uses = lexical_closure(
        func, initial_call=True, recursion_stack=[], forced_dependencies=forced_dependencies
    )
    return closure_source, (formatted_source, cleaned_source), uses


def _unwrap_function(func: Any) -> Tuple[Callable, Optional[Callable]]:
    """
    Recursively unwrap decorated functions to retrieve the original function.

    Returns:
        A tuple containing:
            - The original function.
            - The outermost wrapper function (if any), else None.
    """
    wrappers = []
    while hasattr(func, "__ell_func__"):
        wrappers.append(func)
        func = func.__ell_func__
    return func, wrappers[-1] if wrappers else None


def _get_globals_and_frees(func: Callable) -> Dict[str, Dict[str, Any]]:
    """Retrieve global and free variables of a function."""
    globals_dict = collections.OrderedDict(globalvars(func))
    frees_dict = collections.OrderedDict(dill.detect.freevars(func))

    if isinstance(func, type):
        for method in func.__dict__.values():
            if isinstance(method, (types.FunctionType, types.MethodType)):
                globals_dict.update(collections.OrderedDict(globalvars(method)))
                frees_dict.update(collections.OrderedDict(dill.detect.freevars(method)))

    return {"globals": globals_dict, "frees": frees_dict}


def _process_dependencies(
    func: Callable,
    globals_and_frees: Dict[str, Dict[str, Any]],
    closure: Closure,
    already_closed: Set[int],
    recursion_stack: List[str],
):
    """Process dependencies of a function."""
    if isinstance(func, (types.FunctionType, types.MethodType)):
        _process_default_kwargs(func, closure, already_closed, recursion_stack)

    for var_name, var_value in itertools.chain(
        globals_and_frees["globals"].items(), globals_and_frees["frees"].items()
    ):
        _process_variable(var_name, var_value, closure, already_closed, recursion_stack)


def _process_default_kwargs(
    func: Callable,
    closure: Closure,
    already_closed: Set[int],
    recursion_stack: List[str],
):
    """Process default keyword arguments of a function."""
    for name, param in inspect.signature(func).parameters.items():
        if param.default is not inspect.Parameter.empty:
            _process_dependency(param.default, closure, already_closed, recursion_stack, name=name)


def _process_dependency(
    value: Any,
    closure: Closure,
    already_closed: Set[int],
    recursion_stack: List[str],
    name: Optional[str] = None,
):
    """Process dependencies from function signatures and variables."""
    if name in FORBIDDEN_NAMES:
        return

    try:
        if isinstance(value, (types.FunctionType, type, types.MethodType)):
            dep_source, _, dep_uses = lexical_closure(
                value, already_closed, recursion_stack.copy()
            )
            if dep_source:
                closure.dependencies.append(Dependency(source=dep_source))
            closure.uses.add(value)
            closure.uses.update(dep_uses)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                _process_dependency(item, closure, already_closed, recursion_stack, name=name)
        else:
            is_builtin = getattr(value.__class__, "__module__", "") in {"builtins", "__builtins__"}
            if not is_builtin:
                module_name = value.__class__.__module__
                if should_import(module_name):
                    import_statement = dill.source.getimport(value.__class__, alias=value.__class__.__name__)
                    closure.imports.add(import_statement)
                else:
                    dep_source, _, dep_uses = lexical_closure(
                        type(value), already_closed, recursion_stack.copy()
                    )
                    if dep_source:
                        closure.dependencies.append(Dependency(source=dep_source))
                    closure.uses.update(dep_uses)
    except Exception as e:
        _raise_error(
            f"Failed to capture the lexical closure of dependency {name}",
            e,
            recursion_stack,
        )


def _process_variable(
    var_name: str,
    var_value: Any,
    closure: Closure,
    already_closed: Set[int],
    recursion_stack: List[str],
):
    """Process a single variable."""
    try:
        module = inspect.getmodule(var_value)
        module_name = module.__name__ if module else None
        if module_name and should_import(module_name):
            import_statement = dill.source.getimport(var_value, alias=var_name)
            closure.imports.add(import_statement)
            return
    except Exception:
        pass

    if isinstance(var_value, (types.FunctionType, type, types.MethodType, types.ModuleType, types.BuiltinFunctionType)):
        _handle_special_variable(var_name, var_value, closure, already_closed, recursion_stack)
    else:
        _handle_other_variable(var_name, var_value, closure)


def _handle_special_variable(
    var_name: str,
    var_value: Any,
    closure: Closure,
    already_closed: Set[int],
    recursion_stack: List[str],
):
    """Handle special types of variables like callables and modules."""
    if isinstance(var_value, (types.FunctionType, type, types.MethodType)):
        _process_callable(var_name, var_value, closure, already_closed, recursion_stack)
    elif isinstance(var_value, types.ModuleType):
        _process_module(var_name, var_value, closure)
    elif isinstance(var_value, types.BuiltinFunctionType):
        import_statement = dill.source.getimport(var_value, alias=var_name)
        closure.imports.add(import_statement)


def _process_callable(
    var_name: str,
    var_value: Callable,
    closure: Closure,
    already_closed: Set[int],
    recursion_stack: List[str],
):
    """Process a callable object."""
    try:
        module_name = inspect.getmodule(var_value).__name__
        is_ell_module = "ell" in module_name
    except Exception:
        is_ell_module = False

    if var_name not in FORBIDDEN_NAMES and not is_ell_module:
        try:
            dep_source, _, dep_uses = lexical_closure(
                var_value, already_closed, recursion_stack.copy()
            )
            if dep_source:
                closure.dependencies.append(Dependency(source=dep_source))
            closure.uses.add(var_value)
            closure.uses.update(dep_uses)
        except Exception as e:
            _raise_error(
                f"Failed to capture the lexical closure of global or free variable {var_name}",
                e,
                recursion_stack,
            )


def _process_module(var_name: str, var_value: types.ModuleType, closure: Closure):
    """Process a module."""
    if should_import(var_value.__name__):
        import_statement = dill.source.getimport(var_value, alias=var_name)
        closure.imports.add(import_statement)
    else:
        closure.modules.append(ModuleDependency(name=var_name, value=var_value))


def _handle_other_variable(var_name: str, var_value: Any, closure: Closure):
    """Process non-callable and non-module variables."""
    if isinstance(var_value, str) and "\n" in var_value:
        closure.dependencies.append(Dependency(source=f"{var_name} = {var_value}"))
    elif is_immutable_variable(var_value):
        closure.dependencies.append(Dependency(source=f"#<BV>\n{var_name} = {repr(var_value)}\n#</BV>"))
    else:
        closure.dependencies.append(Dependency(source=f"#<BmV>\n{var_name} = <{type(var_value).__name__} object>\n#</BmV>"))


def _assemble_final_source(closure: Closure) -> str:
    """Assemble the final source code."""
    parts = []
    if closure.imports:
        parts.append("\n".join(sorted(closure.imports)))
    if closure.dependencies:
        parts.append("\n".join(dep.source for dep in closure.dependencies))
    if closure.modules:
        module_sources = []
        for module_dep in closure.modules:
            module_sources.append(f"# Module: {module_dep.name}")
            module_dependencies = "\n".join(dep.source for dep in module_dep.dependencies)
            if module_dependencies:
                module_sources.append(module_dependencies)
        parts.append("\n\n".join(module_sources))
    if closure.source:
        parts.append(closure.source)

    combined = "\n\n".join(parts)

    # Remove duplicate lines while preserving order
    unique_lines = []
    seen = set()
    for line in combined.split("\n"):
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)
    final_source = "\n".join(unique_lines)

    # Replace multiple newlines with two
    final_source = re.sub(r"\n{3,}", "\n\n", final_source)

    return final_source


def _generate_function_hash(source: str, cleaned_source: str, qualname: str) -> str:
    """Generate a unique hash for the function."""
    hash_input = "\n".join((source, cleaned_source, qualname)).encode()
    return "lmp-" + hashlib.md5(hash_input).hexdigest()


def _update_ell_func(
    outer_func: Any,
    source: str,
    cleaned_source: str,
    globals_dict: Dict[str, Any],
    frees_dict: Dict[str, Any],
    function_hash: str,
    uses: Set[Any],
):
    """Update the attributes of the outer function with closure information."""
    formatted_source = format_source(source)
    formatted_cleaned = format_source(cleaned_source)

    # If it's a bound method, set attributes on the underlying function
    if isinstance(outer_func, types.MethodType):
        outer_func = outer_func.__func__

    outer_func.__ell_closure__ = (
        formatted_source,
        formatted_cleaned,
        globals_dict,
        frees_dict,
    )
    outer_func.__ell_hash__ = function_hash
    # Only add ell-decorated functions to __ell_uses__
    ell_uses = {fn for fn in closure.uses if hasattr(fn, "__ell_func__")}
    outer_func.__ell_uses__ = ell_uses


def _raise_error(message: str, exception: Exception, recursion_stack: List[str]):
    """Raise an exception with a detailed message."""
    error_msg = f"{message}. Error: {str(exception)}\nRecursion stack: {' -> '.join(recursion_stack)}"
    raise Exception(error_msg)


def _clean_source(final_source: str) -> str:
    """Clean the source code by removing duplicates and organizing imports."""
    # Replace multiple newlines with two
    cleaned = re.sub(r"\n{3,}", "\n\n", final_source)
    return cleaned
        '''
    ])

