import os
from functools import partial

import networkx as nx
import pandas as pd
from networkx.classes.reportviews import NodeView
from networkx.utils.backends import _registered_algorithms, _load_backend

_IS_TESTING = os.environ.get("NETWORKX_TEST_BACKEND") in {"pandas", "pandas_graph"}


class BackendInterface:
    @staticmethod
    def convert_from_nx(
        G,
        edge_attrs=None,
        node_attrs=None,
        preserve_edge_attrs=False,
        preserve_node_attrs=False,
        preserve_graph_attrs=False,
        name=None,
        graph_name=None,
        *,
        source="source",
        target="target",
        edge_key="edge_key",
    ):
        if isinstance(G, NodeView):
            # Convert to a Graph with only nodes (no edges)--useful when testing
            new_graph = nx.Graph()
            new_graph.add_nodes_from(G.items())
            G = new_graph

        # PERF: optimize all of this! Don't use `nx.to_pandas_edgelist`
        keep_cols = {source, target}
        if G.is_multigraph() and edge_key is not None:
            keep_cols.add(edge_key)
        else:
            edge_key = None
        df = nx.to_pandas_edgelist.orig_func(
            G, source=source, target=target, edge_key=edge_key
        )
        if edge_attrs is not None:
            # Drop unused columns and apply default
            df = df.drop(columns=df.columns.difference(keep_cols | edge_attrs.keys()))
            for edge_attr, edge_default in edge_attrs.items():
                if edge_default is not None and edge_attr in df.columns:
                    df[edge_attr] = df[edge_attr].fillna(edge_default)
        elif not preserve_edge_attrs:
            # Drop data columns
            df = df.drop(columns=df.columns.difference(keep_cols))

        # Handle node attributes
        if preserve_node_attrs:
            node_df = pd.DataFrame.from_dict(G.nodes, orient="index")
            if len(node_df) != len(G):
                node_df = node_df.reindex(G)
        elif node_attrs is not None:
            node_df = pd.DataFrame.from_dict(G.nodes, orient="index")
            node_df = node_df.drop(columns=node_df.columns.difference(node_attrs))
            if len(node_df) != len(G):
                node_df = node_df.reindex(G)
            for node_attr, node_default in node_attrs.items():
                if node_default is not None and node_attr in node_df.columns:
                    node_df[node_attr] = node_df[node_attr].fillna(node_default)
        else:
            node_df = pd.DataFrame(index=G)
        df.nx.node_df = node_df

        # Update `df.nx` attributes
        df.nx.source = source
        df.nx.target = target
        df.nx.is_directed = G.is_directed()
        df.nx.is_multigraph = G.is_multigraph()
        if G.is_multigraph():
            df.nx.edge_key = edge_key
        if preserve_graph_attrs:
            df.nx.graph.update(G.graph)
        return df

    @staticmethod
    def convert_to_nx(obj, *, name=None):
        if isinstance(obj, pd.DataFrame):
            if not hasattr(obj, "__networkx_backend__"):
                return obj
            create_using = (
                (nx.MultiDiGraph if obj.nx.is_directed else nx.MultiGraph)
                if obj.nx.is_multigraph
                else nx.DiGraph if obj.nx.is_directed else nx.Graph
            )
            edge_key = obj.nx.edge_key if obj.nx.is_multigraph else None
            edge_attr = set(obj.columns) - {obj.nx.source, obj.nx.target}
            # This may be necessary for networkx <= 3.3
            if edge_key is not None:
                edge_attr.discard(edge_key)
            G = nx.from_pandas_edgelist(
                obj,
                source=obj.nx.source,
                target=obj.nx.target,
                edge_attr=list(edge_attr) if edge_attr else None,
                edge_key=edge_key,
                create_using=create_using,
            )
            if obj.nx.node_df is not None:
                # Try to maintain iteration order when iterating over nodes
                G_temp = create_using()
                G_temp.add_nodes_from(
                    (k, v.dropna().to_dict()) for k, v in obj.nx.node_df.iterrows()
                )
                if G.is_multigraph():
                    G_temp.add_edges_from(G.edges(data=True, keys=True))
                else:
                    G_temp.add_edges_from(G.edges(data=True))
                G = G_temp
            G.graph.update(obj.nx.graph)
            return G
        return obj

    def __getattr__(self, attr, *, from_backend_name="pandas"):
        if (
            attr not in _registered_algorithms
            or _IS_TESTING  # Avoid infinite recursion when testing
            and attr in {"empty_graph", "from_pandas_edgelist"}
        ):
            raise AttributeError(attr)
        return partial(_auto_func, from_backend_name, attr)


def _auto_func(from_backend_name, func_name, /, *args, **kwargs):
    # Do our own conversion and dispatching based on `nx.config.backend_priority`.
    # We want to refactor dispatching in networkx to make this simpler, and then
    # see if we can do it all (with backend-to-backend conversions) within networkx.
    dfunc = _registered_algorithms[func_name]
    for to_backend_name in nx.config.backend_priority:
        if to_backend_name in {
            "pandas",
            "pandas_graph",
        } or not dfunc.__wrapped__._should_backend_run(
            to_backend_name, *args, **kwargs
        ):
            continue
        try:
            return _run_with_backend(
                from_backend_name, to_backend_name, dfunc, args, kwargs
            )
        except NotImplementedError:
            pass
    return _run_with_backend(from_backend_name, "networkx", dfunc, args, kwargs)


def _run_with_backend(from_backend_name, to_backend_name, dfunc, args, kwargs):
    # Convert graph arguments from pandas to a backend an run with that backend.
    from_backend = _load_backend(from_backend_name)
    if to_backend_name == "networkx":
        to_backend = None
    else:
        to_backend = _load_backend(to_backend_name)
    # Hmm, his gets recomputed for each backend.
    graphs_resolved = {
        gname: val
        for gname, pos in dfunc.graphs.items()
        if (val := args[pos] if pos < len(args) else kwargs.get(gname)) is not None
    }
    func_name = dfunc.name
    if dfunc.list_graphs:
        graphs_converted = {
            gname: (
                [
                    _convert_to_backend(g, from_backend, to_backend, func_name)
                    for g in val
                ]
                if gname in dfunc.list_graphs
                else _convert_to_backend(val, from_backend, to_backend, func_name)
            )
            for gname, val in graphs_resolved.items()
        }
    else:
        graphs_converted = {
            gname: _convert_to_backend(graph, from_backend, to_backend, func_name)
            for gname, graph in graphs_resolved.items()
        }
    converted_args = list(args)
    converted_kwargs = dict(kwargs)
    for gname, val in graphs_converted.items():
        if gname in kwargs:
            converted_kwargs[gname] = val
        else:
            converted_args[dfunc.graphs[gname]] = val
    if to_backend is None:
        backend_func = dfunc.orig_func
    else:
        backend_func = getattr(to_backend, func_name)
    result = backend_func(*converted_args, **converted_kwargs)
    if dfunc._returns_graph:
        # Convert to pandas
        if to_backend is not None:
            result = to_backend.convert_to_nx(result)
        result = from_backend.convert_from_nx(
            result,
            preserve_edge_attrs=True,
            preserve_node_attrs=True,
            preserve_graph_attrs=True,
            name=func_name,
        )
    return result


def _convert_to_backend(G_from, from_backend, to_backend, func_name):
    # TODO: convert directly to known backends instead of converting to nx first.
    # TODO: use __networkx_cache__! Use value from cache if possible, and set to cache.
    Gnx = from_backend.convert_to_nx(G_from)
    if to_backend is None:
        return Gnx
    return to_backend.convert_from_nx(
        Gnx,
        preserve_edge_attrs=True,
        preserve_node_attrs=True,
        preserve_graph_attrs=True,
        name=func_name,
    )


backend_interface = BackendInterface()
