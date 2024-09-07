===========
@ell.simple
===========

.. autofunction:: ell.simple

Usage
-----

The ``@ell.simple`` decorator can be used in two main ways:

1. Using the docstring as the system prompt:

   .. code-block:: python

      @ell.simple(model="gpt-4")
      def hello(name: str):
          """You are a helpful assistant."""
          return f"Say hello to {name}!"

2. Explicitly defining messages:

   .. code-block:: python

      @ell.simple(model="gpt-4")
      def hello(name: str):
          return [
              ell.system("You are a helpful assistant."),
              ell.user(f"Say hello to {name}!")
          ]