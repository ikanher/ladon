from __future__ import annotations

import sqlite3

import pytest
from test_theorem_lineage_store import _test_identity, sample_plan

from ladon.proof_search_schema import create_proof_search_schema
from ladon.theorem_lineage_query import (
    LineageQuery,
    TheoremLineageQueryError,
    query_lineage,
)
from ladon.theorem_lineage_store import ingest_theorem_lineage


def lineage_database() -> tuple[sqlite3.Connection, object]:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    create_proof_search_schema(connection)
    identity = _test_identity()
    ingest_theorem_lineage(connection, sample_plan(), identity)
    return connection, identity


def test_reverse_trust_query_returns_source_to_theorem_route() -> None:
    connection, identity = lineage_database()

    result = query_lineage(
        connection,
        identity,
        LineageQuery(theorem="Demo.target", boundary="trust"),
    )

    assert result["status"] == "available"
    assert result["authority"] == "lean_environment"
    assert result["routes"] == [
        {
            "root": "Classical.choice",
            "target": "Demo.target",
            "depth": 2,
            "nodes": ["Classical.choice", "Demo.helper", "Demo.target"],
            "edges": ["value", "value"],
        }
    ]


def test_edge_kind_filter_and_depth_cap_are_explicit() -> None:
    connection, identity = lineage_database()

    result = query_lineage(
        connection,
        identity,
        LineageQuery(
            theorem="Demo.target",
            boundary="trust",
            edge_kind="type",
            max_depth=1,
        ),
    )

    assert result["routes"] == []
    assert result["query"]["edgeKind"] == "type"
    assert result["bounds"]["maxDepth"] == 1
    assert result["truncated"] is False


def test_missing_or_stale_closure_does_not_fallback() -> None:
    connection, identity = lineage_database()

    missing = query_lineage(
        connection,
        identity,
        LineageQuery(theorem="Demo.unknown", boundary="trust"),
    )
    assert missing["status"] == "unavailable"
    assert missing["reason"] == "not_ingested"

    stale_identity = _test_identity(source_fingerprint="changed")
    stale = query_lineage(
        connection,
        stale_identity,
        LineageQuery(theorem="Demo.target", boundary="trust"),
    )
    assert stale["status"] == "unavailable"
    assert stale["reason"] == "stale-source"


def test_query_rejects_invalid_root_boundary() -> None:
    connection, identity = lineage_database()
    with pytest.raises(TheoremLineageQueryError, match="root"):
        query_lineage(
            connection,
            identity,
            LineageQuery(theorem="Demo.target", boundary="declaration"),
        )


def test_query_uses_forward_and_reverse_lineage_indexes() -> None:
    connection, identity = lineage_database()
    forward = query_lineage(
        connection,
        identity,
        LineageQuery(theorem="Demo.target", boundary="trust", explain=True),
    )
    assert "idx_lineage_edges_forward" in " ".join(forward["queryPlan"])
    assert "idx_lineage_edges_reverse" in " ".join(forward["queryPlan"])


def test_edge_cap_is_reported_without_unbounded_route_output() -> None:
    connection, identity = lineage_database()
    result = query_lineage(
        connection,
        identity,
        LineageQuery(theorem="Demo.target", boundary="trust", max_edges=1),
    )
    assert result["truncated"] is True
    assert result["bounds"]["maxEdges"] == 1
