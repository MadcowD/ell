=============
Configuration
=============

ell2a provides various configuration options to customize its behavior.

.. autofunction:: ell2a.init

This ``init`` function is a convenience function that sets up the configuration for ell2a. It is a thin wrapper around the ``Config`` class, which is a Pydantic model.

You can modify the global configuration using the ``ell2a.config`` object which is an instance of ``Config``:

.. autopydantic_model:: ell2a.Config
    :members:
    :exclude-members: default_client, registry, store
    :model-show-json: false
    :model-show-validator-members: false
    :model-show-config-summary: false
    :model-show-field-summary: false
    :model-show-validator-summary: false