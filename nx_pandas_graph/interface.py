from nx_pandas_graph import classes
from nx_pandas.interface import pandas_backend


class BackendInterface:
    @staticmethod
    def convert_from_nx(*args, **kwargs):
        df = pandas_backend.convert_from_nx(*args, **kwargs)
        graph_class = (
            (classes.MultiDiGraph if df.nx.is_multigraph else classes.DiGraph)
            if df.nx.is_directed
            else classes.MultiGraph if df.nx.is_multigraph else classes.Graph
        )
        return graph_class.from_pandas(df)

    @staticmethod
    def convert_to_nx(obj, *, name=None):
        if getattr(obj, "__networkx_backend__", None) == "pandas_graph":
            obj = obj.df
        return pandas_backend.convert_to_nx(obj, name=name)

    def __getattr__(self, attr):
        return pandas_backend.__getattr__(attr, from_backend_name="pandas_graph")


backend_interface = BackendInterface()
