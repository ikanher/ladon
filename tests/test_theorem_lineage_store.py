from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from ladon.proof_search_schema import create_proof_search_schema
from ladon.theorem_capsule_models import canonical_json_bytes, sha256_bytes
from ladon.theorem_lineage_store import (
    LineageIdentity,
    TheoremLineageError,
    ingest_theorem_lineage,
    inspect_lineage_closure,
    normalize_lineage_plan,
)


def test_normalize_complete_plan_materializes_external_frontier_and_trust() -> None:
    bundle = normalize_lineage_plan(sample_plan())

    assert bundle.target_name == "Demo.target"
    assert {node.name for node in bundle.nodes} == {
        "Classical.choice",
        "Demo.helper",
        "Demo.target",
    }
    assert bundle.edges == (
        {
            "source": "Demo.helper",
            "target": "Classical.choice",
            "kind": "value",
            "targetOwnerModule": "Init.Classical",
            "targetKind": "axiom",
        },
        {
            "source": "Demo.target",
            "target": "Demo.helper",
            "kind": "value",
            "targetOwnerModule": "Demo",
            "targetKind": "theorem",
        },
    )
    assert bundle.trust == (
        {"kind": "axiom_reference", "scope": "value", "target": "Classical.choice"},
    )
    assert len(bundle.scc_members) == 3


def test_normalize_accepts_planner_canonical_closure_fingerprint() -> None:
    plan = sample_plan()
    graph = plan["semanticGraph"]
    graph["closureFingerprint"] = sha256_bytes(
        canonical_json_bytes({"nodes": graph["nodes"], "edges": graph["edges"]})
    )

    bundle = normalize_lineage_plan(plan)

    assert bundle.closure_fingerprint == graph["closureFingerprint"]


def test_normalize_rejects_dangling_source_and_conflicting_duplicate() -> None:
    dangling = sample_plan()
    dangling["semanticGraph"]["edges"].append(
        {
            "source": "Demo.missing",
            "target": "Demo.helper",
            "kind": "value",
            "targetOwnerModule": "Demo",
            "targetKind": "theorem",
        }
    )
    dangling["semanticGraph"]["edgeCount"] = 3
    with pytest.raises(TheoremLineageError, match="source"):
        normalize_lineage_plan(dangling)

    duplicate = sample_plan()
    duplicate["semanticGraph"]["edges"].append(
        {
            "source": "Demo.target",
            "target": "Demo.helper",
            "kind": "value",
            "targetOwnerModule": "Other",
            "targetKind": "theorem",
        }
    )
    duplicate["semanticGraph"]["edgeCount"] = 3
    with pytest.raises(TheoremLineageError, match="duplicate"):
        normalize_lineage_plan(duplicate)


def test_normalize_rejects_partial_or_non_lean_authority() -> None:
    partial = sample_plan()
    partial["semanticGraph"]["status"] = "partial"
    with pytest.raises(TheoremLineageError, match="complete"):
        normalize_lineage_plan(partial)

    wrong_authority = sample_plan()
    wrong_authority["semanticGraph"]["authority"] = "lexical_text"
    with pytest.raises(TheoremLineageError, match="authority"):
        normalize_lineage_plan(wrong_authority)


def test_ingestion_is_constrained_and_status_is_fresh() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    create_proof_search_schema(connection)
    identity = LineageIdentity(
        repository="/tmp/demo",
        source_fingerprint="source",
        configuration_fingerprint="configuration",
        toolchain_identity="lean:v4",
        base_generation_identity="base-generation",
        helper_identity="helper",
        schema_generation="sqlite-v2-fts1-lineage1",
    )

    result = ingest_theorem_lineage(connection, sample_plan(), identity)
    assert result["nodeCount"] == 3
    assert result["edgeCount"] == 2
    status = inspect_lineage_closure(connection, "Demo.target", identity)
    assert status["status"] == "fresh"
    assert status["closureId"] == result["closureId"]
    assert result["storage"]["after"]["allocatedBytes"] >= result["storage"]["before"]["allocatedBytes"]
    assert result["statistics"]["refreshed"] is True
    assert connection.execute(
        "SELECT COUNT(*) FROM sqlite_stat1 WHERE tbl IN ('lineage_edges','lineage_nodes')"
    ).fetchone()[0] >= 2


def test_ingestion_rejects_mismatched_closure_fingerprint() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    create_proof_search_schema(connection)
    identity = LineageIdentity(
        repository="/tmp/demo",
        source_fingerprint="source",
        configuration_fingerprint="configuration",
        toolchain_identity="lean:v4",
        base_generation_identity="base-generation",
        helper_identity="helper",
        schema_generation="sqlite-v2-fts1-lineage1",
    )
    plan = sample_plan()
    plan["semanticGraph"]["closureFingerprint"] = "wrong"
    with pytest.raises(TheoremLineageError, match="fingerprint"):
        ingest_theorem_lineage(connection, plan, identity)
    assert connection.execute("SELECT COUNT(*) FROM lineage_closures").fetchone()[0] == 0


def test_replacement_keeps_other_theorems_and_is_atomic() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    create_proof_search_schema(connection)
    identity = _test_identity()
    first = sample_plan()
    second = sample_plan()
    second["target"]["name"] = "Demo.other"
    second["semanticGraph"]["nodes"][1]["name"] = "Demo.other"
    second["semanticGraph"]["edges"][1]["source"] = "Demo.other"
    second["semanticGraph"]["stronglyConnectedComponents"][2]["component"] = ["Demo.other"]
    second["semanticGraph"]["stronglyConnectedComponents"][2]["members"] = ["Demo.other"]
    second["semanticGraph"]["closureFingerprint"] = ""
    ingest_theorem_lineage(connection, first, identity)
    ingest_theorem_lineage(connection, second, identity)
    replacement = sample_plan()
    replacement["semanticGraph"]["closureFingerprint"] = ""
    ingest_theorem_lineage(connection, replacement, identity)

    rows = connection.execute(
        "SELECT theorem_name, active FROM lineage_closures ORDER BY theorem_name"
    ).fetchall()
    assert rows == [("Demo.other", 1), ("Demo.target", 1)]


def test_size_failure_preserves_active_closure() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    create_proof_search_schema(connection)
    identity = _test_identity()
    ingest_theorem_lineage(connection, sample_plan(), identity)
    before = connection.execute(
        "SELECT closure_id, active FROM lineage_closures WHERE theorem_name = 'Demo.target'"
    ).fetchone()
    with pytest.raises(TheoremLineageError, match="size limit"):
        ingest_theorem_lineage(connection, sample_plan(), identity, max_bytes=1)
    after = connection.execute(
        "SELECT closure_id, active FROM lineage_closures WHERE theorem_name = 'Demo.target'"
    ).fetchone()
    assert after == before


def test_identity_drift_is_reported() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    create_proof_search_schema(connection)
    identity = _test_identity()
    ingest_theorem_lineage(connection, sample_plan(), identity)
    stale = _test_identity(source_fingerprint="changed")
    assert inspect_lineage_closure(connection, "Demo.target", stale)["status"] == "stale-source"


def _test_identity(**overrides: str) -> LineageIdentity:
    values = {
        "repository": "/tmp/demo",
        "source_fingerprint": "source",
        "configuration_fingerprint": "configuration",
        "toolchain_identity": "lean:v4",
        "base_generation_identity": "base-generation",
        "helper_identity": "helper",
        "schema_generation": "sqlite-v2-fts1-lineage1",
    }
    values.update(overrides)
    return LineageIdentity(**values)


def sample_plan() -> dict[str, Any]:
    nodes = [
        {
            "name": "Demo.helper",
            "ownerModule": "Demo",
            "kind": "theorem",
            "compilerGenerated": False,
            "declaredAxiom": False,
            "unsafe": False,
            "typeFingerprint": "helper-type",
            "valueFingerprint": "helper-value",
            "typeDependencies": [],
            "valueDependencies": [
                {
                    "name": "Classical.choice",
                    "ownerModule": "Init.Classical",
                    "kind": "axiom",
                    "declaredAxiom": True,
                    "unsafe": False,
                }
            ],
        },
        {
            "name": "Demo.target",
            "ownerModule": "Demo",
            "kind": "theorem",
            "compilerGenerated": False,
            "declaredAxiom": False,
            "unsafe": False,
            "typeFingerprint": "target-type",
            "valueFingerprint": "target-value",
            "typeDependencies": [],
            "valueDependencies": [
                {
                    "name": "Demo.helper",
                    "ownerModule": "Demo",
                    "kind": "theorem",
                    "declaredAxiom": False,
                    "unsafe": False,
                }
            ],
        },
    ]
    edges = [
        {
            "source": "Demo.helper",
            "target": "Classical.choice",
            "kind": "value",
            "targetOwnerModule": "Init.Classical",
            "targetKind": "axiom",
        },
        {
            "source": "Demo.target",
            "target": "Demo.helper",
            "kind": "value",
            "targetOwnerModule": "Demo",
            "targetKind": "theorem",
        },
    ]
    return {
        "plannerVersion": "test",
        "target": {"name": "Demo.target", "kind": "theorem", "module": "Demo"},
        "semanticGraph": {
            "status": "complete",
            "authority": "lean_environment",
            "nodes": nodes,
            "edges": edges,
            "nodeCount": 2,
            "edgeCount": 2,
            "stronglyConnectedComponents": [
                {"component": ["Classical.choice"], "members": ["Classical.choice"], "cyclic": False},
                {"component": ["Demo.helper"], "members": ["Demo.helper"], "cyclic": False},
                {"component": ["Demo.target"], "members": ["Demo.target"], "cyclic": False},
            ],
            "externalFrontier": [edges[0]],
            "helperChecksum": "checksum",
            "closureFingerprint": "",
            "trustFrontier": [
                {"kind": "axiom_reference", "scope": "value", "target": "Classical.choice"}
            ],
        },
    }
