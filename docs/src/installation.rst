Installation
============

``ell`` and ``ell studio`` are both contained within the ``ell-ai`` python package available on PyPI. You simply need to install the package and set up your API keys.

Installing ell
--------------

1. Install using pip:

   .. code-block:: bash

      pip install -U ell-ai

   By default, this installs only the OpenAI client SDK. If you want to include the Anthropic client SDK, use the "anthropic" extra like so:

   .. code-block:: bash

      pip install -U ell-ai[anthropic]

2. Verify installation:

   .. code-block:: bash

      python -c "import ell; print(ell.__version__)"

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
