"""Frozen TDD contract for closed, artifact-owned v3 subject identities."""

from __future__ import annotations

import copy
import sqlite3
from typing import Any

import pytest
from support.proofir_v3_subject_scope import (
    FOREIGN_ENVIRONMENT,
    UNKNOWN_SCHEME,
    claim,
    derivation,
    external_ref,
)

from ladon import proofir_sqlite_v3, proofir_v3, proofir_v3_queries
from ladon.proofir_v3 import ProofIRV3Error, detached_content_id


def validate_batch(artifacts: list[dict[str, Any]]) -> object:
    implementation = getattr(proofir_v3, "validate_envelope_batch", None)
    assert implementation is not None, "native-v3 batch reference validation is missing"
    return implementation(artifacts)


def semantic_candidates(
    connection: sqlite3.Connection, owner: str, kind: str, local_id: str
) -> list[dict[str, Any]]:
    implementation = getattr(proofir_v3_queries, "query_v3_semantic_candidates", None)
    assert implementation is not None, "semantic candidate query is missing"
    return implementation(
        connection,
        {
            "ownerArtifactId": owner,
            "kind": kind,
            "localId": local_id,
        },
        limit=20,
    )


def memory_database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    proofir_sqlite_v3.create_v3_schema(connection)
    return connection


def _table_columns(
    connection: sqlite3.Connection, table: str
) -> dict[str, sqlite3.Row | tuple[Any, ...]]:
    return {row[1]: row for row in connection.execute(f"PRAGMA table_info({table})")}


def _foreign_keys(
    connection: sqlite3.Connection, table: str
) -> list[sqlite3.Row | tuple[Any, ...]]:
    return list(connection.execute(f"PRAGMA foreign_key_list({table})"))


def _index_columns(connection: sqlite3.Connection, table: str) -> set[tuple[str, ...]]:
    return {
        tuple(info[2] for info in connection.execute(f"PRAGMA index_info({row[1]})"))
        for row in connection.execute(f"PRAGMA index_list({table})")
    }


def _reidentify(value: dict[str, Any]) -> dict[str, Any]:
    value["artifactId"] = detached_content_id(value)
    return value


def _assert_failure(
    artifacts: list[dict[str, Any]], *, code: str, pointer: str
) -> None:
    with pytest.raises(ProofIRV3Error) as captured:
        validate_batch(artifacts)
    assert captured.value.diagnostic.code == code
    assert captured.value.diagnostic.pointer == pointer


def test_local_compact_references_are_closed_under_the_enclosing_artifact() -> None:
    artifact = claim()
    checked = validate_batch([artifact])
    assert checked

    bad = copy.deepcopy(artifact)
    bad["payload"]["statementRef"] = {
        "kind": "statement",
        "localId": "statement:missing",
    }
    _reidentify(bad)
    _assert_failure(
        [bad],
        code="dangling-local-reference",
        pointer="/payload/statementRef",
    )


def test_same_local_ids_in_distinct_owner_artifacts_do_not_join() -> None:
    left = claim(fingerprint="sha256:" + "1" * 64)
    right = claim(fingerprint="sha256:" + "2" * 64)
    assert left["artifactId"] != right["artifactId"]
    validate_batch([left, right])

    connection = memory_database()
    proofir_sqlite_v3.project_envelopes(connection, [left, right])
    rows = connection.execute(
        "SELECT owner_content_artifact_id,subject_kind,local_id "
        "FROM proofir_v3_subjects WHERE local_id='statement:goal' "
        "ORDER BY owner_content_artifact_id"
    ).fetchall()
    assert rows == [
        (left["artifactId"], "statement", "statement:goal"),
        (right["artifactId"], "statement", "statement:goal"),
    ]


def test_supported_fingerprint_candidate_does_not_merge_exact_subjects() -> None:
    left = claim(fingerprint="sha256:" + "3" * 64)
    right = claim(fingerprint="sha256:" + "3" * 64)
    right["producer"]["buildDigest"] = "sha256:" + "c" * 64
    _reidentify(right)
    assert left["artifactId"] != right["artifactId"]
    connection = memory_database()
    proofir_sqlite_v3.project_envelopes(connection, [left, right])

    candidates = semantic_candidates(
        connection, left["artifactId"], "statement", "statement:goal"
    )
    assert candidates == [
        {
            "ownerArtifactId": right["artifactId"],
            "kind": "statement",
            "localId": "statement:goal",
            "basis": "supported-fingerprint",
        }
    ]
    assert connection.execute(
        "SELECT COUNT(*) FROM proofir_v3_subjects WHERE local_id='statement:goal'"
    ).fetchone() == (2,)


def test_search_and_opaque_subject_metadata_round_trip_without_becoming_identity() -> (
    None
):
    artifact = claim()
    subject = artifact["subjectRefs"][0]
    subject["searchShape"] = {"head": "Fixture.goal", "arity": 2}
    subject["opaquePayloadRef"] = "sha256:" + "d" * 64
    _reidentify(artifact)

    checked = validate_batch([artifact])
    assert checked[0].to_dict()["subjectRefs"][0]["searchShape"] == {
        "head": "Fixture.goal",
        "arity": 2,
    }

    connection = memory_database()
    proofir_sqlite_v3.project_envelopes(connection, [artifact])
    row = connection.execute(
        "SELECT search_shape_json,opaque_payload_ref FROM proofir_v3_subjects "
        "WHERE owner_content_artifact_id=? AND subject_kind='statement' "
        "AND local_id='statement:goal'",
        (artifact["artifactId"],),
    ).fetchone()
    assert row == ('{"arity":2,"head":"Fixture.goal"}', "sha256:" + "d" * 64)

    same_identity = claim()
    same_identity["subjectRefs"][0]["searchShape"] = {"head": "Other.goal"}
    same_identity["subjectRefs"][0]["opaquePayloadRef"] = "sha256:" + "e" * 64
    assert (
        same_identity["subjectRefs"][0]["fingerprint"]
        == artifact["subjectRefs"][0]["fingerprint"]
    )


def test_unknown_fingerprint_scheme_is_opaque_and_cannot_establish_equality() -> None:
    left = claim(fingerprint="sha256:" + "4" * 64, scheme=UNKNOWN_SCHEME)
    right = claim(fingerprint="sha256:" + "4" * 64, scheme=UNKNOWN_SCHEME)
    connection = memory_database()
    proofir_sqlite_v3.project_envelopes(connection, [left, right])
    assert (
        semantic_candidates(
            connection, left["artifactId"], "statement", "statement:goal"
        )
        == []
    )


def test_external_reference_requires_present_exact_owner_and_target_descriptor() -> (
    None
):
    target = claim()
    dependent = claim(local_id="statement:dependent")
    dependent["payload"]["statementRef"] = external_ref(
        target["artifactId"], "statement", "statement:goal"
    )
    _reidentify(dependent)

    _assert_failure(
        [dependent],
        code="external-artifact-not-in-batch",
        pointer="/payload/statementRef/artifactRef",
    )
    assert validate_batch([target, dependent])

    missing_local = copy.deepcopy(dependent)
    missing_local["payload"]["statementRef"]["localId"] = "statement:missing"
    _reidentify(missing_local)
    _assert_failure(
        [target, missing_local],
        code="external-subject-not-found",
        pointer="/payload/statementRef",
    )

    missing_kind = copy.deepcopy(dependent)
    missing_kind["payload"]["statementRef"]["kind"] = "declaration"
    _reidentify(missing_kind)
    _assert_failure(
        [target, missing_kind],
        code="unexpected-reference-kind",
        pointer="/payload/statementRef/kind",
    )


def test_external_semantic_reference_rejects_environment_mismatch_and_self_reference() -> (
    None
):
    foreign = claim(environment=FOREIGN_ENVIRONMENT)
    dependent = claim(local_id="statement:dependent")
    dependent["payload"]["statementRef"] = external_ref(
        foreign["artifactId"], "statement", "statement:goal"
    )
    _reidentify(dependent)
    _assert_failure(
        [foreign, dependent],
        code="external-reference-environment-mismatch",
        pointer="/payload/statementRef",
    )

    self_referential = claim()
    self_referential["payload"]["statementRef"] = external_ref(
        self_referential["artifactId"], "statement", "statement:goal"
    )
    # The stale content ID is intentional: rejection must happen before any attempt at a
    # self-referential hash fixed point.
    _assert_failure(
        [self_referential],
        code="self-external-reference",
        pointer="/payload/statementRef/artifactRef",
    )


def test_same_step_and_context_ids_in_distinct_derivations_remain_owner_scoped() -> (
    None
):
    left = derivation(derivation_id="derivation:left")
    right = derivation(derivation_id="derivation:right")
    assert left["artifactId"] != right["artifactId"]
    validate_batch([left, right])
    connection = memory_database()
    proofir_sqlite_v3.project_envelopes(connection, [left, right])
    assert connection.execute(
        "SELECT COUNT(*) FROM proofir_v3_derivation_steps "
        "WHERE step_local_id='step:shared'"
    ).fetchone() == (2,)
    assert connection.execute(
        "SELECT COUNT(*) FROM proofir_v3_subjects "
        "WHERE subject_kind='local-context' AND local_id='context:shared'"
    ).fetchone() == (2,)


def test_sqlite_schema_uses_owner_in_subject_key_fks_indexes_and_revision() -> None:
    connection = memory_database()
    assert proofir_sqlite_v3.V3_SCHEMA_VERSION >= 3
    columns = _table_columns(connection, "proofir_v3_subjects")
    assert "owner_content_artifact_id" in columns
    pk = [row[1] for row in sorted(columns.values(), key=lambda row: row[5]) if row[5]]
    assert pk == ["owner_content_artifact_id", "subject_kind", "local_id"]
    foreign_keys = _foreign_keys(connection, "proofir_v3_subjects")
    assert any(
        row[3] == "owner_content_artifact_id"
        and row[2] == "proofir_v3_artifacts"
        and row[4] == "content_artifact_id"
        for row in foreign_keys
    )
    claim_columns = _table_columns(connection, "proofir_v3_claims")
    assert "statement_owner_artifact_id" in claim_columns
    claim_fks = _foreign_keys(connection, "proofir_v3_claims")
    assert any(
        row[3] == "statement_owner_artifact_id" and row[2] == "proofir_v3_subjects"
        for row in claim_fks
    )
    index_columns = _index_columns(connection, "proofir_v3_claims")
    assert any(
        index[:3]
        == ("statement_owner_artifact_id", "statement_kind", "statement_local_id")
        for index in index_columns
    )


def test_schema_rejects_obsolete_global_subject_database_instead_of_adapting_it() -> (
    None
):
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE proofir_v3_subjects("
        "environment_ref TEXT NOT NULL,subject_kind TEXT NOT NULL,local_id TEXT NOT NULL,"
        "PRIMARY KEY(environment_ref,subject_kind,local_id))"
    )
    with pytest.raises((RuntimeError, ValueError, sqlite3.DatabaseError)):
        proofir_sqlite_v3.create_v3_schema(connection)
