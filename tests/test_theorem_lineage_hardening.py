from __future__ import annotations

import time

from support.first_hand_fixtures import CLOSURE_ID, THEOREM, populated_connection

from ladon.proof_search_baselines import SqlTraceCounter
from ladon.theorem_lineage_query import LineageQuery, query_lineage
from ladon.theorem_lineage_store import LineageIdentity
from ladon.theorem_lineage_summary import summarize_lineage


def fixture_identity() -> LineageIdentity:
    return LineageIdentity(
        repository="/fixture",
        source_fingerprint="source",
        configuration_fingerprint="config",
        toolchain_identity="lean",
        base_generation_identity="base",
        helper_identity="helper",
        schema_generation="schema",
    )


def test_lineage_query_plan_has_frontier_key_in_recursive_step() -> None:
    result = query_lineage(
        populated_connection(edge_fanout=4, edge_layers=3),
        fixture_identity(),
        LineageQuery(theorem=THEOREM, boundary="trust", explain=True, max_depth=3, max_nodes=64),
    )
    plans = " ".join(result["queryPlan"])
    assert "PRIMARY KEY (closure_id=? AND source=?)" in plans
    assert "closure_id=? AND source=?" in plans
    assert "closure_id=? AND target=?" in plans


def test_lineage_acquisition_reports_finite_cap_and_preserves_authority() -> None:
    result = query_lineage(
        populated_connection(edge_fanout=8, edge_layers=5),
        fixture_identity(),
        LineageQuery(theorem=THEOREM, boundary="trust", max_depth=5, max_nodes=32, recursive_row_limit=64),
    )
    assert result["authority"] == "lean_environment"
    assert result["acquisition"]["rowsObserved"] <= 33
    assert result["bounds"]["recursiveRowLimit"] == 64
    assert result["truncated"] is True


def test_lineage_summary_is_constant_shape_and_does_not_walk_routes() -> None:
    connection = populated_connection(edge_fanout=4, edge_layers=3)
    counter = SqlTraceCounter().attach(connection)
    result = summarize_lineage(connection, fixture_identity(), THEOREM)
    counter.detach()
    assert result["status"] == "available"
    assert result["closureId"] == CLOSURE_ID
    assert result["nodes"]["total"] > 1
    assert result["edges"]["value"] > 0
    assert result["storage"]["allocatedBytes"] > 0
    assert result["limits"]["policy"] == "not-configured"
    assert not any("WITH RECURSIVE" in statement for statement in counter.statements)
    assert counter.count <= 10


def test_frontier_first_fixture_query_is_fast_and_repeatable() -> None:
    connection = populated_connection(edge_fanout=8, edge_layers=5)
    query = LineageQuery(theorem=THEOREM, boundary="trust", max_depth=4, max_nodes=100, max_edges=400, max_routes=5)
    first_started = time.monotonic()
    first = query_lineage(connection, fixture_identity(), query)
    first_elapsed = time.monotonic() - first_started
    second_started = time.monotonic()
    second = query_lineage(connection, fixture_identity(), query)
    second_elapsed = time.monotonic() - second_started
    assert first["status"] == second["status"] == "available"
    assert first["routes"] == second["routes"]
    assert first_elapsed < 1.0
    assert second_elapsed < 1.0
