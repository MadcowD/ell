try:
    import fastapi
    import ell.stores
except ImportError:
    raise ImportError("ell.studio is missing dependencies. Install them with `pip install -U ell-ai[studio]. More info: https://docs.ell.so/installation/custom-installation")