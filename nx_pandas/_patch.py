import pandas as pd


# https://pandas.pydata.org/docs/development/extending.html#registering-custom-accessors
@pd.api.extensions.register_dataframe_accessor("nx")
class NxAccessor:
    def __init__(self, pandas_obj):
        self._df = pandas_obj
        self.is_directed = True
        self.is_multigraph = False
        self._source = "source" if "source" in pandas_obj.columns else None
        self._target = "target" if "target" in pandas_obj.columns else None
        self._edge_key = "edge_key" if "edge_key" in pandas_obj.columns else None
        self.node_df = None
        self.graph = {}  # `df.nx.graph` instead of `df.graph`
        self._cache = None

    @property
    def source(self):
        if self._source is not None and self._source not in self._df.columns:
            # Should we raise here to ensure consistency or let users break themselves?
            raise KeyError(
                f"DataFrame does not have column {self._source!r}. "
                "`df.nx.source` must be set to an existing column name "
                "for the DataFrame to be used as a networkx graph."
            )
        return self._source

    @source.setter
    def source(self, val):
        if val is not None and val not in self._df.columns:
            raise KeyError(
                f"DataFrame does not have column {val!r}. "
                "`df.nx.source` must be set to an existing column name "
                "for the DataFrame to be used as a networkx graph."
            )
        self._source = val

    @property
    def target(self):
        if self._target is not None and self._target not in self._df.columns:
            raise KeyError(
                f"DataFrame does not have column {self._target!r}. "
                "`df.nx.target` must be set to an existing column name "
                "for the DataFrame to be used as a networkx graph."
            )
        return self._target

    @target.setter
    def target(self, val):
        if val is not None and val not in self._df.columns:
            raise KeyError(
                f"DataFrame does not have column {val!r}. "
                "`df.nx.target` must be set to an existing column name "
                "for the DataFrame to be used as a networkx graph."
            )
        self._target = val

    @property
    def edge_key(self):
        if not self.is_multigraph:
            raise AttributeError("'edge_key' attribute only exists for multigraphs")
        if self._edge_key is not None and self._edge_key not in self._df.columns:
            raise KeyError(
                f"DataFrame does not have column {self._edge_key!r}. "
                "`df.nx.edge_key` must be set to an existing column name or None "
                "for the DataFrame to be used as a networkx multi-graph."
            )
        return self._edge_key

    @edge_key.setter
    def edge_key(self, val):
        if not self.is_multigraph:
            raise AttributeError("'edge_key' attribute only exists for multigraphs")
        if val is not None and val not in self._df.columns:
            raise KeyError(
                f"DataFrame does not have column {val!r}. "
                "`df.nx.edge_key` must be set to an existing column name or None "
                "for the DataFrame to be used as a networkx multi-graph."
            )
        self._edge_key = val

    @property
    def cache_enabled(self):
        return self._cache is not None

    @cache_enabled.setter
    def cache_enabled(self, val):
        if not val:
            # Wipe out the cache when disabling the cache
            self._cache = None
        elif self._cache is None:
            # Enable cache if necessary
            self._cache = {}

    def __dir__(self):
        attrs = super().__dir__()
        if not self.is_multigraph:
            attrs.remove("edge_key")
        return attrs


def _attr_raise_if_invalid_graph(df, attr):
    try:
        df.nx.source
        df.nx.target
        if df.nx.is_multigraph:
            df.nx.edge_key
    except KeyError as exc:
        raise AttributeError(
            f"{type(df).__name__!r} object has no attribute '{attr}'"
        ) from exc
    if df.nx._source is None:
        raise AttributeError(
            f"{type(df).__name__!r} object has no attribute '{attr}'.\n\n"
            "`df.nx.source` (currently None) must be set to an existing "
            "column name for the DataFrame to be used as a networkx graph."
        )
    if df.nx._target is None:
        raise AttributeError(
            f"{type(df).__name__!r} object has no attribute '{attr}'.\n\n"
            "`df.nx.target` (currently None) must be set to an existing "
            "column name for the DataFrame to be used as a networkx graph."
        )


def __networkx_backend__(self):
    # `df.__networkx_backend__` only available if `df` is a valid graph
    _attr_raise_if_invalid_graph(self, "__networkx_backend__")
    return "pandas"


def __networkx_cache__(self):
    # `df.__networkx_cache__` only available if `df` is a valid graph
    _attr_raise_if_invalid_graph(self, "__networkx_cache__")
    return self.nx._cache


def is_directed(self):
    """Returns True if graph is directed, False otherwise."""
    return self.nx.is_directed


def is_directed_property(self):
    """Returns True if graph is directed, False otherwise."""
    # `df.is_directed` only available if `df` is a valid graph
    _attr_raise_if_invalid_graph(self, "is_directed")
    return is_directed.__get__(self)


def is_multigraph(self):
    """Returns True if graph is a multigraph, False otherwise."""
    return self.nx.is_multigraph


def is_multigraph_property(self):
    """Returns True if graph is a multigraph, False otherwise."""
    # `df.is_multigraph` only available if `df` is a valid graph
    _attr_raise_if_invalid_graph(self, "is_multigraph")
    return is_multigraph.__get__(self)


pd.DataFrame.__networkx_backend__ = property(__networkx_backend__)
pd.DataFrame.__networkx_cache__ = property(__networkx_cache__)
# Add `is_directed` and `is_multigraph` so `not_implemented_for` decorator works
pd.DataFrame.is_directed = property(is_directed_property)
pd.DataFrame.is_multigraph = property(is_multigraph_property)


def get_info():
    # Should we add config for e.g. default source, target, edge_key columns?
    # Maybe config to enable/disable cache by default?
    return {}
