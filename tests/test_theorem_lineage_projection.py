from __future__ import annotations

import pytest
from test_theorem_lineage_query import lineage_database

from ladon.theorem_lineage_algorithms import (
    AlgorithmInputError,
    compute_dominators,
    unfold_tree,
)
from ladon.theorem_lineage_projection import (
    ProjectionQuery,
    TheoremLineageProjectionError,
    project_lineage,
)
from ladon.theorem_lineage_query import LineageQuery


def test_route_projection_is_authoritative_and_render_neutral() -> None:
    connection, identity = lineage_database()
    result = project_lineage(
        connection,
        identity,
        ProjectionQuery(lineage=LineageQuery(theorem="Demo.target", boundary="trust")),
    )
    assert result["status"] == "available"
    assert result["authority"] == "lean_environment"
    assert result["routes"][0]["nodes"] == ["Classical.choice", "Demo.helper", "Demo.target"]
    assert "possible proof" not in result["nonclaim"].lower()
    assert "alternative proofs" in result["nonclaim"]


def test_bottleneck_algorithm_reports_mandatory_chain_and_bypass() -> None:
    nodes = ("root", "join", "target")
    edges = (("root", "join"), ("join", "target"))
    result = compute_dominators(nodes, edges, ("root",), "target")
    assert result["chain"] == ["root", "join", "target"]
    bypass = compute_dominators(nodes, edges + (("root", "target"),), ("root",), "target")
    assert bypass["chain"] == ["root", "target"]


def test_bottleneck_projection_returns_bounded_summary_not_full_map() -> None:
    connection, identity = lineage_database()
    result = project_lineage(
        connection,
        identity,
        ProjectionQuery(
            lineage=LineageQuery(theorem="Demo.target", boundary="trust"),
            view="bottlenecks",
            max_dominator_rows=1,
        ),
    )["bottlenecks"]
    assert "dominators" not in result
    assert result["dominatorReturned"] == 1
    assert result["dominatorSummaryTruncated"] is True


def test_bottleneck_projection_explains_missing_bounded_route(monkeypatch) -> None:
    connection, identity = lineage_database()
    monkeypatch.setattr(
        "ladon.theorem_lineage_projection.query_lineage",
        lambda *_args: {
            "status": "available",
            "nodes": [],
            "routes": [],
            "nonclaim": "bounded fixture",
        },
    )
    with pytest.raises(
        TheoremLineageProjectionError,
        match="run --view summary first.*--max-nodes/--max-routes",
    ):
        project_lineage(
            connection,
            identity,
            ProjectionQuery(
                lineage=LineageQuery(theorem="Demo.target"),
                view="bottlenecks",
            ),
        )


def test_tree_unfolding_marks_shared_nodes_and_caps() -> None:
    tree = unfold_tree(
        ("root", "target"),
        (
            ("root", "left"),
            ("root", "right"),
            ("left", "shared"),
            ("right", "shared"),
            ("shared", "target"),
        ),
        max_nodes=4,
    )
    assert tree["references"]
    assert tree["omissions"]
    try:
        unfold_tree(("root",), (), max_nodes=0)
    except AlgorithmInputError:
        pass
    else:
        raise AssertionError("expected explicit algorithm cap failure")


def test_projection_is_stable_for_reordered_query_rows() -> None:
    connection, identity = lineage_database()
    first = project_lineage(
        connection,
        identity,
        ProjectionQuery(lineage=LineageQuery(theorem="Demo.target", boundary="trust")),
    )
    second = project_lineage(
        connection,
        identity,
        ProjectionQuery(lineage=LineageQuery(theorem="Demo.target", boundary="trust")),
    )
    assert first["nodes"] == second["nodes"]
    assert first["routes"] == second["routes"]
