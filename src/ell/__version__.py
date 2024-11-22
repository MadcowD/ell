from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ell-ai")
except PackageNotFoundError:
    __version__ = "unknown"