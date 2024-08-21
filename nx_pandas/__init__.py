import importlib.metadata

# This package *must* be installed even for local development,
# so checking version like this lets us be strict and informative.
try:
    __version__ = importlib.metadata.version("nx-pandas")
except Exception as exc:
    raise AttributeError(
        "`nx_pandas.__version__` not available. This may mean "
        "nx-pandas was incorrectly installed or not installed at all. "
        "For local development, you may want to do an editable install via "
        "`python -m pip install -e path/to/nx-pandas`"
    ) from exc
del importlib
