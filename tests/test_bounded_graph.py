from __future__ import annotations

import pytest

from ladon.bounded_graph import (
    GraphRequest,
    bounded_bfs,
    bounded_paths,
    brute_force_dominators,
    dominators,
    normalize_graph,
    strongly_connected_components,
    unfold_dag,
)


def graph(edges: tuple[tuple[str, str], ...], nodes: tuple[str, ...] = ("a", "b", "c", "d")):
    return normalize_graph(GraphRequest(nodes=nodes, edges=edges))


def test_normalization_is_stable_and_reports_malformed_edges() -> None:
    result = normalize_graph(GraphRequest(nodes=("b", "a"), edges=(("a", "b"), ("a", "x"))))
    assert result.nodes == ("a", "b")
    assert result.node_ids == {"a": 0, "b": 1}
    assert result.forward["a"] == ("b",)
    assert result.omissions[0]["reason"] == "endpoint_not_indexed"


def test_bfs_and_paths_are_bounded_and_cycle_safe() -> None:
    result = graph((("a", "b"), ("b", "c"), ("c", "a"), ("a", "d")))
    assert bounded_bfs(result, ("a",), max_depth=1) == ("a", "b", "d")
    assert bounded_paths(result, "a", "c", max_depth=4) == (("a", "b", "c"),)


def test_scc_and_dominators_handle_diamond_and_cycle() -> None:
    result = graph((("a", "b"), ("a", "c"), ("b", "d"), ("c", "d"), ("d", "d")))
    assert ("a",) in strongly_connected_components(result)
    assert dominators(result, ("a",))["d"] == frozenset({"a", "d"})
    assert dominators(result, ("a",)) == brute_force_dominators(result, ("a",))
    cycle = graph((("a", "b"), ("b", "a")))
    assert ("a", "b") in strongly_connected_components(cycle)
    assert unfold_dag(cycle)["references"][0]["kind"] == "cycle"


def test_disconnected_nodes_are_explicitly_unreachable() -> None:
    result = graph((("a", "b"),))
    assert dominators(result, ("a",))["c"] == frozenset()


def test_graph_caps_are_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_graph(GraphRequest(nodes=("a",), edges=(), max_depth=0))
