=============
Configuration
=============

ell provides various configuration options to customize its behavior.

.. autofunction:: ell.init

This ``init`` function is a convenience function that sets up the configuration for ell. It is a thin wrapper around the ``Config`` class, which is a Pydantic model.

You can modify the global configuration using the ``ell.config`` object which is an instance of ``Config``:

.. autopydantic_model:: ell.Config
    :members:
    :exclude-members: default_client, registry, store
    :model-show-json: false
    :model-show-validator-members: false
    :model-show-config-summary: false
    :model-show-field-summary: false
    :model-show-validator-summary: false