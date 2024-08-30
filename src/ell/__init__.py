"""
ell: A Lightweight, Functional Prompt Engineering Framework
===========================================================

ell is a Python library that provides a novel approach to prompt engineering
and interaction with language models. It is built on the principles that
prompts are programs, not just strings, and that every interaction with a
language model is valuable.

Key Features
------------

1. Functional approach to prompt engineering
2. Visualization, tracking, and versioning of prompts using ell-studio
3. Support for various storage backends (SQLite, PostgreSQL)
4. Integration with popular language models

Main Components
---------------

- Language Model Programs (LMPs): Discrete subroutines for interacting with language models
- Storage backends: For persisting and analyzing interactions
- ell-studio: A visualization tool for tracking prompt engineering processes

Example Usage
-------------

Here's a simple example of how to use ell::

    import ell

    @ell.lm(model="gpt-4")
    def generate_poem(topic: str):
        '''You are a helpful assistant that writes poems.'''
        return f"Write a short poem about {topic}."

    # Use SQLite as the storage backend
    store = ell.SQLiteStore('my_project')
    store.install(autocommit=True)

    # Generate a poem
    poem = generate_poem("autumn leaves")
    print(poem)

    # Visualize your prompt engineering process
    # Run in terminal: python -m ell.studio --storage-dir ./my_project

For more detailed information, refer to the specific module documentation:

- ``ell.lmp``: Language Model Program decorators and utilities
- ``ell.types``: Type definitions for messages and content blocks
- ``ell.models``: Supported language models
- ``ell.configurator``: Configuration utilities

"""


from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import system, user, assistant
from ell.__version__ import __version__

# Import all models
import ell.models

# Import everything from configurator
from ell.configurator import *

__all__ = [
    'simple',
    'tool',
    'complex',
    'Message',
    'ContentBlock',
    'system',
    'user',
    'assistant',
    '__version__',
]



