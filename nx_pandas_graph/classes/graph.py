import networkx as nx

__all__ = ["Graph"]


class Graph:
    __networkx_backend__ = "pandas_graph"

    def __new__(cls, incoming_graph_data=None, **attr):
        if incoming_graph_data is None:
            new_graph = object.__new__(cls)
        elif incoming_graph_data.__class__ is cls:
            new_graph = incoming_graph_data.copy()
        elif incoming_graph_data.__class__ is cls.to_networkx_class():
            from nx_pandas_graph.interface import backend_interface

            new_graph = backend_interface.convert_from_nx(
                incoming_graph_data,
                preserve_edge_attrs=True,
                preserve_node_attrs=True,
                preserve_graph_attrs=True,
            )
        else:
            raise NotImplementedError
        new_graph.graph.update(attr)
        return new_graph

    #
    # Class methods
    #
    @classmethod
    def from_pandas(cls, df, *, copy=None):
        if df.__networkx_backend__ != "pandas":
            raise TypeError
        new_graph = object.__new__(cls)
        new_graph.df = df
        if (
            copy
            or df.nx.is_directed != cls.is_directed()
            or df.nx.is_multigraph != cls.is_multigraph()
        ):
            if copy is False:
                raise ValueError(
                    f"Unable to avoid copy while creating a {cls.__name__} as "
                    f"requested.\nUse `{cls.__name__}.from_pandas(df, copy=None)` "
                    "(copy=None is the default) to allow a copy when needed."
                )
            new_graph = new_graph.copy()
            new_graph.df.nx.is_directed = cls.is_directed()
            new_graph.df.nx.is_multigraph = cls.is_multigraph()
        return new_graph

    @classmethod
    def is_directed(cls):
        return False

    @classmethod
    def is_multigraph(cls):
        return False

    @classmethod
    def to_directed_class(cls):
        from .digraph import DiGraph

        return DiGraph

    @classmethod
    def to_networkx_class(cls):
        return nx.Graph

    @classmethod
    def to_undirected_class(cls):
        return Graph

    #
    # Properties
    #
    name = nx.Graph.name

    @property
    def graph(self):
        return self.df.nx.graph

    @graph.setter
    def graph(self, val):
        self.df.nx.graph = val

    #
    # Graph methods
    #
    def copy(self, as_view=False):
        new_graph = object.__new__(self.__class__)
        df = self.df
        if not as_view:
            df_orig = df
            df = df_orig.copy()
            for attr in ["_source", "_target", "_edge_key"]:
                setattr(df.nx, attr, getattr(df_orig.nx, attr))
            for attr in ["graph", "_cache", "node_df"]:
                val = getattr(df_orig.nx, attr)
                if val is not None:
                    setattr(df.nx, attr, val.copy())
        new_graph.df = df
        return new_graph
