import networkx as nx  # noqa: F401
import pandas as pd
import pytest


@pytest.fixture
def df():
    return pd.DataFrame({"source": [0, 1, 2], "target": [1, 2, 0], "foo": [2, 0, 1]})


def test_defaults(df):
    assert df.nx.source == "source"
    assert df.nx.target == "target"
    assert df.nx.is_directed is True
    assert df.nx.is_multigraph is False
    assert df.nx.cache_enabled is False


def test_df_attrs(df):
    assert "nx" in dir(df)
    assert df.__networkx_backend__ == "pandas"
    assert df.__networkx_cache__ is None
    assert df.is_directed() is True
    assert df.is_multigraph() is False


def test_cache_attrs(df):
    # Cache is enabled/disabled via an attribute, which controls the cache
    assert df.__networkx_cache__ is None
    df.nx.cache_enabled = True
    assert df.__networkx_cache__ == {}
    df.__networkx_cache__["x"] = "y"
    df.nx.cache_enabled = True  # no-op
    assert df.__networkx_cache__ == {"x": "y"}
    df.nx.cache_enabled = False
    assert df.__networkx_cache__ is None
    df.nx.cache_enabled = True
    assert df.__networkx_cache__ == {}  # Got reset


def test_edge_key_attr(df):
    # `edge_key` only exists for multigraphs
    assert not hasattr(df.nx, "edge_key")
    assert "edge_key" not in dir(df.nx)
    with pytest.raises(AttributeError, match="only exists for multigraphs"):
        df.nx.edge_key = None
    df.nx.is_multigraph = True
    assert df.nx.is_multigraph is True
    assert df.is_multigraph() is True
    assert hasattr(df.nx, "edge_key")
    assert "edge_key" in dir(df.nx)
    assert df.nx.edge_key is None
    with pytest.raises(KeyError, match="DataFrame does not have column 'bad'"):
        df.nx.edge_key = "bad"
    df.nx.edge_key = "foo"
    assert df.nx.edge_key == "foo"
    df.nx.edge_key = None


@pytest.mark.parametrize("col", ["source", "target"])
def test_invalid_graph(df, col):
    del df[col]
    with pytest.raises(AttributeError, match="to be used as a networkx graph"):
        df.__networkx_backend__
    with pytest.raises(AttributeError, match="to be used as a networkx graph"):
        df.__networkx_cache__
    with pytest.raises(AttributeError, match="to be used as a networkx graph"):
        df.is_directed
    with pytest.raises(AttributeError, match="to be used as a networkx graph"):
        df.is_multigraph
    # If source/target is bad column name, then AttributeError is caused by KeyError
    setattr(df.nx, f"_{col}", "bad")
    with pytest.raises(AttributeError, match="has no attribute") as exc_info:
        df.__networkx_backend__
    assert type(exc_info.value.__cause__) is KeyError
    assert "DataFrame does not have column 'bad'" in exc_info.value.__cause__.args[0]
    with pytest.raises(KeyError, match="DataFrame does not have column 'bad'"):
        raise exc_info.value.__cause__


def test_invalid_graph_edge_key(df):
    df.nx.is_multigraph = True
    df.nx._edge_key = "bad"
    with pytest.raises(KeyError, match="DataFrame does not have column 'bad'"):
        df.nx.edge_key


def test_setattr_column_must_exist(df):
    with pytest.raises(KeyError, match="DataFrame does not have column 'bad'"):
        df.nx.source = "bad"
    with pytest.raises(KeyError, match="DataFrame does not have column 'bad'"):
        df.nx.target = "bad"
    df.nx.is_multigraph = True
    with pytest.raises(KeyError, match="DataFrame does not have column 'bad'"):
        df.nx.edge_key = "bad"


def test_set_attrs(df):
    df.nx.source = "target"
    df.nx.target = "source"
    assert df.nx.source == "target"
    assert df.nx.target == "source"
    assert df.__networkx_backend__ == "pandas"
    df.nx.is_multigraph = True
    df.nx.edge_key = "foo"
    assert df.__networkx_backend__ == "pandas"
    # May be set to None, but is an invalid graph
    df.nx.source = None
    df.nx.target = None
    df.nx.edge_key = None
    with pytest.raises(AttributeError, match="to be used as a networkx graph"):
        df.__networkx_backend__


def test_set_properties(df):
    df2 = df.nx.set_properties(
        source="target",
        target="source",
        edge_key="foo",
        is_directed=False,
        is_multigraph=True,
        cache_enabled=True,
    )
    assert df is df2
    assert df.nx.source == "target"
    assert df.nx.target == "source"
    assert df.nx.edge_key == "foo"
    assert df.nx.is_directed is False
    assert df.nx.is_multigraph is True
    assert df.nx.cache_enabled is True
    with pytest.raises(
        AttributeError, match="'edge_key' attribute only exists for multigraphs"
    ):
        df.nx.set_properties(
            source="source",
            target="target",
            is_directed=True,
            is_multigraph=False,
            cache_enabled=False,
            edge_key="BAD",
        )
    # Unchanged
    assert df.nx.source == "target"
    assert df.nx.target == "source"
    assert df.nx.edge_key == "foo"
    assert df.nx.is_directed is False
    assert df.nx.is_multigraph is True
    assert df.nx.cache_enabled is True
