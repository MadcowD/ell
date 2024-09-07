========================
Models & API Clients
========================

ell supports various language models and API clients.

.. code-block:: python

   import ell
   from ell.clients import OpenAIClient

   client = OpenAIClient(api_key="your-api-key")

   @ell.simple(model="gpt-4", client=client)
   def custom_client_example(prompt: str):
       return prompt