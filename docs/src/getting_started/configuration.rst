Configuring ell
===============

Proper configuration is crucial for getting the most out of ell. This guide will walk you through the process of setting up ell for your project, including storage configuration for versioning and tracing.

Basic Configuration
-------------------

To initialize ell with basic settings, use the ``ell.init()`` function in your project:

.. code-block:: python

    import ell

    ell.init(
        store='./logdir',
        verbose=True,
        autocommit=True
    )

Let's break down these parameters:

- ``store``: Specifies the directory for storing versioning and tracing data.
- ``verbose``: When set to ``True``, enables detailed logging of ell operations.
- ``autocommit``: When ``True``, automatically saves versions and traces.

Storage Configuration
---------------------

ell uses a storage backend to keep track of LMP versions and invocations. By default, it uses a local SQLite database. To set up storage:

.. code-block:: python

    ell.set_store('./logdir', autocommit=True)

This creates a SQLite database in the ``./logdir`` directory. For production environments, you might want to use a more robust database like PostgreSQL:

.. code-block:: python

    from ell.stores.sql import PostgresStore

    postgres_store = PostgresStore("postgresql://user:password@localhost/db_name")
    ell.set_store(postgres_store, autocommit=True)

Customizing Default Parameters
------------------------------

You can set default parameters for your language model calls:

.. code-block:: python

    ell.set_default_lm_params(
        temperature=0.7,
        max_tokens=150
    )

These parameters will be used as defaults for all LMPs unless overridden.

Setting a Default System Prompt
-------------------------------

To set a default system prompt for all your LMPs:

.. code-block:: python

    ell.set_default_system_prompt("You are a helpful AI assistant.")


Advanced Configuration
----------------------

For more advanced use cases, you can configure ell to use specific OpenAI clients for different models:

.. code-block:: python

    import openai

    gpt4_client = openai.Client(api_key="your-gpt4-api-key")
    gpt3_client = openai.Client(api_key="your-gpt3-api-key")

    ell.config.register_model("gpt-4", gpt4_client)
    ell.config.register_model("gpt-3.5-turbo", gpt3_client)

Configuration Best Practices
----------------------------

1. Always set up proper storage for versioning and tracing in production environments.
2. Use environment variables for sensitive information like API keys.
3. Configure logging to help with debugging and monitoring.
4. Set sensible defaults for language model parameters to ensure consistent behavior across your project.

By properly configuring ell, you'll be able to leverage its full capabilities and streamline your development process. Remember to adjust these settings as your project grows and your needs evolve.