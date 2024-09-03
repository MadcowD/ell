Installation
============

This guide will walk you through the process of installing ell on your system.

Steps
------

1. **Install ell using pip:**

   Open your terminal or command prompt and run the following command:

   .. code-block:: bash

      pip install ell

   This will download and install the latest stable version of ell and its dependencies.

2. **Verify the installation:**

   After the installation is complete, you can verify that ell was installed correctly by running:

   .. code-block:: bash

      python -c "import ell; print(ell.__version__)"

   This should print the version number of ell that you just installed.


Setting Up API Keys
-------------------

To use ``ell`` with various language models, you'll need to set up API keys for the models you want to use. Below are the steps to configure API keys for OpenAI and Anthropic.

1. **OpenAI API Key:**

   To use OpenAI's models, you need an API key from OpenAI. Follow these steps:

   a. Sign up or log in to your OpenAI account at https://beta.openai.com/signup/.

   b. Navigate to the API section and generate a new API key.

   c. Set the API key as an environment variable:

      - On Windows:
        Open Command Prompt and run:

        .. code-block:: batch

           setx OPENAI_API_KEY "your-openai-api-key"

      - On macOS and Linux:
        Add the following line to your shell profile (e.g., `.bashrc`, `.zshrc`):

        .. code-block:: bash

           export OPENAI_API_KEY='your-openai-api-key'

   d. Restart your terminal or command prompt to apply the changes.

2. **Anthropic API Key:**

   To use Anthropic's models, you need an API key from Anthropic. Follow these steps:

   a. Sign up or log in to your Anthropic account at https://www.anthropic.com/.

   b. Navigate to the API section and generate a new API key.

   c. Set the API key as an environment variable:

      - On Windows:
        Open Command Prompt and run:

        .. code-block:: batch

           setx ANTHROPIC_API_KEY "your-anthropic-api-key"

      - On macOS and Linux:
        Add the following line to your shell profile (e.g., `.bashrc`, `.zshrc`):

        .. code-block:: bash

           export ANTHROPIC_API_KEY='your-anthropic-api-key'

   d. Restart your terminal or command prompt to apply the changes.

Once you have set up your API keys, ell will automatically use them to access the respective language models. You are now ready to start creating and running Language Model Programs with ell!



Troubleshooting Installation Issues
-----------------------------------

If you encounter any issues during installation, try the following:

1. Ensure you have the latest version of pip:

   .. code-block:: bash

      pip install --upgrade pip

2. If you're using a virtual environment, make sure it's activated before installing ell.

3. On some systems, you may need to use ``pip3`` instead of ``pip`` to ensure you're using Python 3.

4. If you encounter permission errors, you may need to use ``sudo`` on Unix-based systems or run your command prompt as an administrator on Windows.

If you continue to have problems, please check the Troubleshooting section of this documentation or file an issue on the ell GitHub repository.

Next Steps
----------

Now that you have ell installed, you're ready to start using it! Head over to the Getting Started guide to create your first Language Model Program.