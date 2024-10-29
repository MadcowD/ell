try:
    import sqlmodel
except ImportError:
    raise ImportError("ell.stores: Missing --extras (sqlite|postgres). Add them with poetry add ell[sqlite] or pip install -e ell[sqlite]")
