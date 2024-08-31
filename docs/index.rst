.. ell documentation master file, created by
   sphinx-quickstart on Thu Aug 29 13:45:32 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================
ell documentation
=================

Welcome to the documentation for ``ell``, a lightweight, functional prompt engineering framework.

Overview
--------

``ell`` is built on a few core principles:

1. **Prompts are programs, not strings**: In ``ell``, we think of using a language model as a discrete subroutine called a **language model program** (LMP).

2. **Prompts are parameters of a machine learning model**: ``ell`` treats prompts as learnable parameters.

3. **Every call to a language model is valuable**: ``ell`` emphasizes the importance of each language model interaction.

Key Features
------------

- Functional approach to prompt engineering
- Visualization and tracking of prompts using ``ell-studio``
- Support for various storage backends (SQLite, PostgreSQL)
- Integration with popular language models

For installation instructions, usage examples, and contribution guidelines, please refer to the project's GitHub repository.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   reference/index
