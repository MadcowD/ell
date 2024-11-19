try:
    import sqlmodel
except ImportError:
    raise ImportError("ell.stores has missing dependencies. Install them with `pip install -U ell-ai[sqlite]` or `pip install -U ell-ai[postgres]`. More info: https://docs.ell.so/installation/custom-installation")
