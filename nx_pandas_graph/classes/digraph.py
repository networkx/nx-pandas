import networkx as nx
from .graph import Graph

__all__ = ["DiGraph"]


class DiGraph(Graph):
    @classmethod
    def is_directed(cls):
        return True

    @classmethod
    def to_networkx_class(cls):
        return nx.DiGraph
