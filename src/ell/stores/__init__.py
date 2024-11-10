try:
    # TODO. this will actually be ok once we have stores that do not require sqlmodel, so we may not want to rely on it now
    # or have a stores.sql module later
    import sqlmodel
except ImportError:
    raise ImportError("ell.stores has missing dependencies. Install them with `pip install -U ell-ai[sqlite]` or `pip install -U ell-ai[postgres]`. More info: https://docs.ell.so/installation/custom-installation")
