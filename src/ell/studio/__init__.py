try:
    import fastapi
    import ell.stores
except ImportError:
    raise ImportError("ell.studio requires fastapi, ell.stores to be installed. Install with --extras studio,sqlite|postgres")