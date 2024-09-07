============
@ell.complex
============

.. autofunction:: ell.complex

Usage
-----

The ``@ell.complex`` decorator is used for more advanced scenarios:

.. code-block:: python

   @ell.complex(model="gpt-4", tools=[some_tool])
   def complex_task(input: str):
       return [
           ell.system("You are an AI capable of using tools."),
           ell.user(f"Perform this task: {input}")
       ]