import networkx as nx
from .digraph import DiGraph
from .multigraph import MultiGraph

__all__ = ["MultiDiGraph"]


class MultiDiGraph(MultiGraph, DiGraph):
    @classmethod
    def is_directed(cls):
        return True

    @classmethod
    def to_networkx_class(cls):
        return nx.MultiDiGraph
