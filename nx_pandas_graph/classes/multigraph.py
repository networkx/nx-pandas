import networkx as nx
from .graph import Graph

__all__ = ["MultiGraph"]


class MultiGraph(Graph):

    @classmethod
    def is_multigraph(cls):
        return True

    @classmethod
    def to_directed_class(cls):
        from .multidigraph import MultiDiGraph

        return MultiDiGraph

    @classmethod
    def to_networkx_class(cls):
        return nx.MultiGraph

    @classmethod
    def to_undirected_class(cls):
        return MultiGraph
