from __future__ import annotations

import json
from pathlib import Path

from support.first_hand_fixtures import (
    CLOSURE_ID,
    THEOREM,
    coverage_connection,
    database_resource_snapshot,
    fixture_fingerprint,
    owner_projection_fixture,
    populated_connection,
    query_plan,
    table_counts,
)

from ladon.proof_difference import DifferenceRequest, analyze_difference
from ladon.proof_search_constructor import ConstructorRequest, constructor_coverage
from ladon.proof_search_consumers import ConsumerRequest, query_consumers

MANIFEST = Path(__file__).parent / "fixtures/proof_search_baselines/first-hand-baseline-v1.json"
PLAN_CONTRACT = Path(__file__).parent / "fixtures/proof_search_baselines/plan-contract-v1.json"


def test_first_hand_manifest_is_identity_bearing_and_has_downstream_owners() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema"] == "ladon-first-hand-baseline-manifest-v1"
    assert payload["sqlite"]["databaseBytesAfterLineage"] > payload["sqlite"]["baseBuildMaxBytes"]
    assert set(payload["knownRedOwners"]) == {
        "consumerCoverage", "constructorCoverage", "binderDifference", "lineagePlan",
        "storagePolicy", "schemaRightsizing", "proofirAccessPaths", "rankingAndProjection",
    }


def test_plan_contract_and_resource_snapshot_are_machine_readable() -> None:
    contract = json.loads(PLAN_CONTRACT.read_text(encoding="utf-8"))
    assert contract["schema"] == "ladon-first-hand-plan-contract-v1"
    connection = populated_connection(edge_fanout=4, edge_layers=3)
    snapshot = database_resource_snapshot(
        connection,
        ("declarations", "lineage_edges", "lineage_nodes"),
    )
    assert snapshot["allocatedBytes"] > 0
    assert snapshot["rowCounts"]["lineage_edges"] > 0
    assert isinstance(snapshot["objectBytes"], dict)


def test_populated_fixture_is_deterministic_and_exercises_all_core_relations() -> None:
    first = populated_connection()
    second = populated_connection()
    assert fixture_fingerprint(first) == fixture_fingerprint(second)
    counts = table_counts(first)
    assert counts["lineage_nodes"] > 100
    assert counts["lineage_edges"] > 1000
    assert owner_projection_fixture()["selectedModules"] == ["Fixture.OwnerA", "Fixture.OwnerB"]


def test_baseline_captures_the_current_lineage_closure_scan_shape() -> None:
    connection = populated_connection(edge_fanout=8, edge_layers=5)
    plan = query_plan(
        connection,
        """WITH RECURSIVE walk(node, depth) AS (
            SELECT ?, 0
            UNION ALL
            SELECT e.target, walk.depth + 1
            FROM walk JOIN lineage_edges e ON e.closure_id = ? AND e.source = walk.node
            WHERE walk.depth < 2 LIMIT 1000
        ) SELECT node FROM walk""",
        (THEOREM, CLOSURE_ID),
    )
    assert any("lineage_edges" in row for row in plan)
    assert not any("closure_id=? AND source=?" in row for row in plan)


def test_consumer_red_contract_exposes_missing_semantic_population() -> None:
    connection = coverage_connection("lexical")
    result = query_consumers(connection, ConsumerRequest(THEOREM))
    assert result["status"] == "not-populated"


def test_constructor_red_contract_does_not_call_empty_fields_available() -> None:
    result = constructor_coverage(ConstructorRequest("Fixture.Record"), ())
    assert result["status"] == "unavailable"
    assert result["coverage"]["status"] == "structure-fields-not-indexed"


def test_explain_red_contract_peels_conclusion_and_keeps_two_residuals() -> None:
    result = analyze_difference(
        DifferenceRequest(
            "firstExitCrossingMass family j region n = terminalExitProbability family j region n",
            "(family : Family) (j : Index) (hregion : Region j) (hinitial : Initial family j) : firstExitCrossingMass family j region n = terminalExitProbability family j region n",
        )
    )
    assert result["classification"] == "rendered-conclusion-with-binders"
    assert len(result["residuals"]) == 4
