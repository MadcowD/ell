Installation
============

``ell`` and ``ell studio`` are both contained within the ``ell-ai`` python package available on PyPI. You simply need to install the package and set up your API keys.

Installing ell
--------------

1. Install using pip:

   .. code-block:: bash

      pip install -U ell-ai[all]

   This installs ``ell``, ``ell-studio``, versioning and tracing with SQLite, and the default provider clients.

2. Verify installation:

   .. code-block:: bash

      python -c "import ell; print(ell.__version__)"

Custom Installation
-------------------

You can create a custom ``ell`` installation with the following options.

Install ``ell`` without storage or ``ell-studio`` and with the default OpenAI client:

.. code-block:: bash

   pip install -U ell-ai

Supported options:

``anthropic``
~~~~~~~~~~~~~
Adds the Anthropic client.

.. code-block:: bash

   pip install -U ell-ai[anthropic]


``groq``
~~~~~~~~
Adds the Groq client.

.. code-block:: bash

   pip install -U ell-ai[groq]


``studio``
~~~~~~~~~~
Adds ``ell-studio``.

.. code-block:: bash

   pip install -U ell-ai[studio]


``sqlite``
~~~~~~~~~~
SQLite storage for versioning and tracing.

.. code-block:: bash

   pip install -U ell-ai[sqlite]


``postgres``
~~~~~~~~~~~~
Postgres storage for versioning and tracing.

Include this option if you'd like to use ``ell-studio`` with Postgres.

.. code-block:: bash

   pip install -U ell-ai[postgres]

Combining options
~~~~~~~~~~~~~~~~~

All options are additive and can be combined as needed.

Example: Install ``ell`` with ``ell-studio``, Postgres, and the Anthropic client:

.. code-block:: bash

   pip install -U ell-ai[studio, postgres, anthropic]


API Key Setup
-------------

OpenAI API Key
~~~~~~~~~~~~~~

1. Get API key from https://platform.openai.com/account/api-keys
2. Install the OpenAI Python package:

   .. code-block:: bash

      pip install openai

3. Set environment variable:

   - Windows:

     .. code-block:: batch

        setx OPENAI_API_KEY "your-openai-api-key"

   - macOS/Linux: 

     .. code-block:: bash

        # in your .bashrc or .zshrc
        export OPENAI_API_KEY='your-openai-api-key'

Anthropic API Key
~~~~~~~~~~~~~~~~~

1. Get API key from https://www.anthropic.com/
2. Install the Anthropic Python package:

   .. code-block:: bash

      pip install anthropic

3. Set environment variable:

   - Windows:

     .. code-block:: batch

        setx ANTHROPIC_API_KEY "your-anthropic-api-key"

   - macOS/Linux:

     .. code-block:: bash

        # in your .bashrc or .zshrc
        export ANTHROPIC_API_KEY='your-anthropic-api-key'

Troubleshooting
---------------

- Update pip: ``pip install --upgrade pip``
- Use virtual environment
- Try ``pip3`` instead of ``pip``
- Use ``sudo`` (Unix) or run as administrator (Windows) if permission errors occur

For more help, see the Troubleshooting section or file an issue on GitHub.

Next Steps
----------

Proceed to the Getting Started guide to create your first Language Model Program.
