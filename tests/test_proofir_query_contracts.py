from __future__ import annotations

import sqlite3

import pytest
from support.proofir_v3_native import native_artifacts

from ladon.proofir_sqlite_v3 import create_v3_schema, project_envelopes
from ladon.proofir_v3_queries import (
    query_v3_artifacts,
    query_v3_semantic_candidates,
    query_v3_theorem_evidence,
    query_v3_triage,
)


@pytest.fixture()
def connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    project_envelopes(connection, [native_artifacts()["proofir.claim"]])
    return connection


@pytest.mark.parametrize("query", [query_v3_triage, query_v3_artifacts])
def test_public_queries_reject_nonpositive_limits(query, connection) -> None:
    with pytest.raises(ValueError, match="invalid query limit"):
        if query is query_v3_triage:
            query(connection, limit=0)
        else:
            query(connection, "anything", limit=-1)


def test_theorem_dossier_exposes_exact_or_bounded_match_accounting(connection) -> None:
    dossier = query_v3_theorem_evidence(connection, "statement:goal", limit=1)
    for section in ("subjects", "claims", "observations", "derivations", "navigation"):
        assert "matchedExact" in dossier[section]
        assert dossier[section]["matched"] >= dossier[section]["returned"]


def test_semantic_candidate_query_rejects_nonpositive_limit(connection) -> None:
    with pytest.raises(ValueError, match="invalid query limit"):
        query_v3_semantic_candidates(
            connection,
            {"ownerArtifactId": "sha256:" + "a" * 64, "kind": "statement", "localId": "statement:goal"},
            limit=-1,
        )


def test_dossier_subject_queries_are_set_oriented() -> None:
    import copy
    from pathlib import Path

    from ladon.proofir_v3 import detached_content_id

    first = native_artifacts()["proofir.claim"]
    second = copy.deepcopy(first)
    second["producer"]["name"] = "second"
    second["artifactId"] = detached_content_id(second)
    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    project_envelopes(connection, [first, second])
    traces: list[str] = []
    connection.set_trace_callback(traces.append)
    query_v3_theorem_evidence(connection, "statement:goal", limit=10)
    selects = [row for row in traces if row.lstrip().upper().startswith("SELECT")]
    assert len(selects) <= 12
    contract = Path("docs/proofir-v3-reference-families.md").read_text(encoding="utf-8")
    assert "Only topology edges" in contract


def test_subject_filter_uses_connection_local_relation_for_large_slices() -> None:
    from ladon.proofir_v3_queries import _subject_predicate

    connection = sqlite3.connect(":memory:")
    subjects = [
        {
            "ownerArtifactId": f"sha256:{index:064x}",
            "kind": "statement",
            "localId": f"statement:{index}",
        }
        for index in range(1200)
    ]
    predicate, parameters = _subject_predicate(
        connection,
        subjects,
        "owner_content_artifact_id",
        "subject_kind",
        "subject_local_id",
    )
    assert parameters == []
    connection.execute(
        "CREATE TABLE dummy (owner_content_artifact_id TEXT, subject_kind TEXT, subject_local_id TEXT)"
    )
    connection.execute(
        "INSERT INTO dummy VALUES (?,?,?)",
        (subjects[0]["ownerArtifactId"], subjects[0]["kind"], subjects[0]["localId"]),
    )
    assert connection.execute(
        f"SELECT COUNT(*) FROM dummy WHERE {predicate}", parameters
    ).fetchone() == (1,)


def test_derivation_occurrence_order_is_stable_under_reverse_unordered_selects() -> None:
    from ladon.proofir_v3_queries import query_v3_theorem_evidence

    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    project_envelopes(connection, [native_artifacts()["proofir.derivation"]])
    observed = []
    for mode in ("OFF", "ON"):
        connection.execute(f"PRAGMA reverse_unordered_selects={mode}")
        dossier = query_v3_theorem_evidence(connection, "statement:goal", limit=20)
        observed.append(dossier["derivations"]["rows"][0]["premiseRefs"])
    assert observed[0] == observed[1]


def test_dossier_preserves_limitations_from_derivation_artifacts() -> None:
    import copy

    from ladon.proofir_v3 import detached_content_id

    derivation = copy.deepcopy(native_artifacts()["proofir.derivation"])
    derivation["limitations"].append(
        {"id": "custom-critical", "message": "derivation interpretation bound"}
    )
    derivation["artifactId"] = detached_content_id(derivation)
    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    project_envelopes(connection, [derivation])
    dossier = query_v3_theorem_evidence(connection, "statement:goal", limit=20)
    assert "custom-critical" in {
        row["id"] for row in dossier["limitations"]["rows"]
    }
