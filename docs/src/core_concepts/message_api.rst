===========
Message API
===========

The Message API in ell provides a structured way to interact with language models.

.. code-block:: python

   from ell import Message, system, user, assistant

   messages = [
       system("You are a helpful assistant."),
       user("Hello, how are you?"),
       assistant("I'm doing well, thank you! How can I assist you today?")
   ]