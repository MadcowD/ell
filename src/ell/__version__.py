from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ell")
except PackageNotFoundError:
    __version__ = "unknown"