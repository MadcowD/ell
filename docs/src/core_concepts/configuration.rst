=============
Configuration
=============

ell provides various configuration options to customize its behavior.

.. code-block:: python

   import ell

   ell.init(
       store='./logdir',
       autocommit=True,
       verbose=True
   )

   # Your ell code here