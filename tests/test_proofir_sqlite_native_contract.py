from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path

import pytest
from support.proofir_v3_native import (
    ENVIRONMENT,
    attachment_set_artifact,
    attempt_log_artifact,
    claim_artifact,
    environment_artifact,
    native_artifacts,
    ref,
)

from ladon import proofir_sqlite_v3
from ladon.proofir_attachment_policy import POLICY_VERSION, resolve_attachment
from ladon.proofir_v3 import MAX_COLLECTION_ITEMS, ProofIRV3Error, detached_content_id

REQUIRED_INDEXES = getattr(proofir_sqlite_v3, "REQUIRED_INDEXES", frozenset())
REQUIRED_TABLES = getattr(proofir_sqlite_v3, "REQUIRED_TABLES", frozenset())
create_v3_schema = proofir_sqlite_v3.create_v3_schema
project_envelopes = proofir_sqlite_v3.project_envelopes
projection_counts = proofir_sqlite_v3.projection_counts
validate_v3_database = proofir_sqlite_v3.validate_v3_database


def publish_v3_database(*args: object, **kwargs: object) -> object:
    implementation = getattr(proofir_sqlite_v3, "publish_v3_database", None)
    assert implementation is not None, "native-v3 atomic publication is missing"
    return implementation(*args, **kwargs)


EXPECTED_TABLES = frozenset(
    {
        "proofir_v3_artifacts",
        "proofir_v3_environments",
        "proofir_v3_subjects",
        "proofir_v3_artifact_subjects",
        "proofir_v3_claims",
        "proofir_v3_derivations",
        "proofir_v3_derivation_sccs",
        "proofir_v3_scc_members",
        "proofir_v3_derivation_steps",
        "proofir_v3_step_premises",
        "proofir_v3_step_conclusions",
        "proofir_v3_substitutions",
        "proofir_v3_plans",
        "proofir_v3_plan_steps",
        "proofir_v3_attempt_logs",
        "proofir_v3_attempts",
        "proofir_v3_attempt_residuals",
        "proofir_v3_check_runs",
        "proofir_v3_check_results",
        "proofir_v3_source_maps",
        "proofir_v3_surfaces",
        "proofir_v3_attachment_sets",
        "proofir_v3_attachments",
        "proofir_v3_attachment_candidates",
        "proofir_v3_observations",
        "proofir_v3_coverage",
        "proofir_v3_omissions",
        "proofir_v3_extensions",
    }
)


def memory_database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    create_v3_schema(connection)
    return connection


def schema_objects(connection: sqlite3.Connection, kind: str) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type = ? AND name NOT LIKE 'sqlite_%'",
            (kind,),
        )
    }


def index_columns(connection: sqlite3.Connection, table: str) -> list[tuple[str, ...]]:
    result = []
    for row in connection.execute(f"PRAGMA index_list({table})"):
        result.append(
            tuple(
                str(info[2])
                for info in connection.execute(f"PRAGMA index_info({row[1]})")
            )
        )
    return result


def test_schema_has_every_normalized_family_and_declared_index() -> None:
    connection = memory_database()
    assert REQUIRED_TABLES == EXPECTED_TABLES
    assert EXPECTED_TABLES <= schema_objects(connection, "table")
    assert REQUIRED_INDEXES <= schema_objects(connection, "index")
    assert "proofir_v3_legacy_artifacts" not in schema_objects(connection, "table")
    assert not {
        "proofir_surfaces",
        "proofir_claims",
        "proofir_surface_claims",
        "proofir_replays",
        "proofir_dags",
        "proofir_dag_nodes",
        "proofir_dag_edges",
        "proofir_dag_witnesses",
        "proofir_claim_dag_links",
        "proofir_attachments",
    } & schema_objects(connection, "table")


def test_every_foreign_key_child_prefix_has_an_index() -> None:
    connection = memory_database()
    for table in sorted(EXPECTED_TABLES):
        foreign_keys = connection.execute(
            f"PRAGMA foreign_key_list({table})"
        ).fetchall()
        child_columns: dict[int, list[tuple[int, str]]] = {}
        for row in foreign_keys:
            child_columns.setdefault(int(row[0]), []).append((int(row[1]), str(row[3])))
        available = index_columns(connection, table)
        for columns in child_columns.values():
            ordered = tuple(column for _, column in sorted(columns))
            assert any(index[: len(ordered)] == ordered for index in available), (
                table,
                ordered,
                available,
            )


def test_constraints_reject_bad_json_negative_ordinals_and_orphans() -> None:
    connection = memory_database()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO proofir_v3_artifacts VALUES (?, ?, ?, ?, ?, ?)",
            (
                "sha256:" + "a" * 64,
                "proofir.claim",
                "3.0",
                "sha256:" + "e" * 64,
                "{",
                "/",
            ),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
                INSERT INTO proofir_v3_step_premises(
                    content_artifact_id, step_local_id, ordinal,
                    owner_content_artifact_id, subject_kind,
                    subject_local_id, source_pointer
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("missing", "step", -1, "env", "statement", "S", "/payload"),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
                INSERT INTO proofir_v3_claims(
                    content_artifact_id, claim_id, statement_owner_artifact_id,
                    statement_kind, statement_local_id, assertion_state, source_pointer
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("missing", "claim", "env", "statement", "S", "asserted", "/payload"),
        )


def test_projection_validates_before_writing_and_rolls_back_on_failure() -> None:
    connection = memory_database()
    valid = claim_artifact()
    project_envelopes(connection, [valid])
    before = projection_counts(connection)

    invalid = copy.deepcopy(valid)
    invalid["payload"]["assertionState"] = "verified"
    invalid["artifactId"] = detached_content_id(invalid)
    with pytest.raises(ProofIRV3Error):
        project_envelopes(connection, [invalid])
    assert projection_counts(connection) == before


def test_rebuild_is_complete_and_stale_rows_do_not_survive() -> None:
    connection = memory_database()
    first = native_artifacts()["proofir.claim"]
    project_envelopes(connection, [first])
    first_id = first["artifactId"]

    second = native_artifacts()["proofir.governance-observation"]
    project_envelopes(connection, [second])
    observed = {
        row[0]
        for row in connection.execute(
            "SELECT content_artifact_id FROM proofir_v3_artifacts"
        )
    }
    assert observed == {second["artifactId"]}
    assert first_id not in observed


def test_local_observation_identity_is_artifact_scoped_without_overwrite() -> None:
    first = native_artifacts()["proofir.governance-observation"]
    second = copy.deepcopy(first)
    second["payload"]["details"] = {"policyId": "review:2"}
    second["artifactId"] = detached_content_id(second)
    assert first["payload"]["observationId"] == second["payload"]["observationId"]
    assert first["artifactId"] != second["artifactId"]

    connection = memory_database()
    project_envelopes(connection, [first, second])
    rows = connection.execute(
        """
        SELECT content_artifact_id, observation_id
        FROM proofir_v3_observations
        ORDER BY content_artifact_id
        """
    ).fetchall()
    assert rows == sorted(
        [
            (first["artifactId"], "observation:1"),
            (second["artifactId"], "observation:1"),
        ]
    )


def test_environment_manifest_is_resolved_without_fabricated_placeholders() -> None:
    manifest = environment_artifact()
    ordinary = claim_artifact()
    connection = memory_database()
    project_envelopes(connection, [manifest, ordinary])

    resolved = connection.execute(
        """
        SELECT manifest_artifact_id, environment_json, resolution_state
        FROM proofir_v3_environments WHERE environment_ref = ?
        """,
        (manifest["environmentRef"],),
    ).fetchone()
    assert resolved == (
        manifest["artifactId"],
        json.dumps(manifest["payload"], sort_keys=True, separators=(",", ":")),
        "resolved",
    )

    unresolved = connection.execute(
        """
        SELECT manifest_artifact_id, environment_json, resolution_state
        FROM proofir_v3_environments WHERE environment_ref = ?
        """,
        (ENVIRONMENT,),
    ).fetchone()
    assert unresolved == (None, None, "unresolved")


def test_owner_scope_is_part_of_subject_and_claim_identity() -> None:
    connection = memory_database()
    project_envelopes(connection, [claim_artifact()])
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
                INSERT INTO proofir_v3_claims(
                    content_artifact_id, claim_id, statement_owner_artifact_id,
                    statement_kind, statement_local_id, assertion_state, source_pointer
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_artifact()["artifactId"],
                "claim:foreign",
                "sha256:" + "f" * 64,
                "statement",
                "statement:goal",
                "asserted",
                "/payload",
            ),
        )


def test_all_native_families_project_with_source_pointer_provenance() -> None:
    artifacts = list(native_artifacts().values())
    connection = memory_database()
    counts = project_envelopes(connection, artifacts)
    assert counts["artifacts"] == len(artifacts)
    for table in EXPECTED_TABLES - {
        "proofir_v3_omissions",
        "proofir_v3_derivation_sccs",
        "proofir_v3_scc_members",
    }:
        assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] > 0, (
            table
        )
    for table in EXPECTED_TABLES - {
        "proofir_v3_artifacts",
        "proofir_v3_environments",
        "proofir_v3_subjects",
        "proofir_v3_coverage",
        "proofir_v3_extensions",
        "proofir_v3_omissions",
    }:
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        assert "source_pointer" in columns, table

    assert connection.execute(
        "SELECT source_pointer FROM proofir_v3_step_premises ORDER BY ordinal"
    ).fetchall() == [
        ("/payload/steps/0/premiseRefs/0",),
        ("/payload/steps/0/premiseRefs/1",),
    ]
    assert connection.execute(
        "SELECT source_pointer FROM proofir_v3_attempt_residuals ORDER BY ordinal"
    ).fetchall() == [("/payload/summary/residualPremiseRefs/0",)]
    assert connection.execute(
        "SELECT source_pointer FROM proofir_v3_attachment_candidates ORDER BY ordinal"
    ).fetchall() == [("/payload/attachments/0/candidates/0",)]


def test_projection_preserves_all_attachment_candidates_and_attempt_residuals() -> None:
    attachment = attachment_set_artifact()
    second_surface = ref("surface", "surface:2")
    attachment["subjectRefs"].append(second_surface)
    attachment["payload"]["attachments"][0]["candidates"].append(
        {
            "declarationId": "declaration:ambiguous",
            "sourceRef": second_surface,
            "method": "name-only-diagnostic",
            "confidence": "none",
            "freshness": "unknown",
            "rank": 6,
            "policyVersion": POLICY_VERSION,
            "decisiveEvidence": [{"kind": "declarationName", "value": "goal"}],
            "rejectionReasons": ["name-only-is-not-an-attachment"],
        }
    )
    attachment["payload"]["attachments"][0]["rejectionReasons"] = ["ambiguous-name"]
    attachment["artifactId"] = detached_content_id(attachment)

    attempts = attempt_log_artifact()
    second_residual = ref("statement", "statement:residual-2")
    attempts["subjectRefs"].append(second_residual)
    attempts["payload"]["summary"]["residualPremiseRefs"].append(second_residual)
    attempts["artifactId"] = detached_content_id(attempts)

    connection = memory_database()
    project_envelopes(connection, [attachment, attempts])
    assert connection.execute(
        """
        SELECT ordinal, source_local_id, declaration_id, method, confidence,
               freshness, rank, policy_version,
               decisive_evidence_json, rejection_reasons_json
        FROM proofir_v3_attachment_candidates ORDER BY ordinal
        """
    ).fetchall() == [
        (
            0,
            "surface:1",
            "declaration:Fixture.goal",
            "environment-fingerprint",
            "exact",
            "fresh",
            0,
            POLICY_VERSION,
            json.dumps(
                [{"kind": "environmentRef", "value": ENVIRONMENT}],
                sort_keys=True,
                separators=(",", ":"),
            ),
            "[]",
        ),
        (
            1,
            "surface:2",
            "declaration:ambiguous",
            "name-only-diagnostic",
            "none",
            "unknown",
            6,
            POLICY_VERSION,
            '[{"kind":"declarationName","value":"goal"}]',
            '["name-only-is-not-an-attachment"]',
        ),
    ]
    assert connection.execute(
        """
        SELECT ordinal, subject_local_id
        FROM proofir_v3_attempt_residuals ORDER BY ordinal
        """
    ).fetchall() == [
        (0, "statement:residual"),
        (1, "statement:residual-2"),
    ]


def test_ambiguous_attachment_projects_no_selected_source_or_semantic_acceptance() -> None:
    artifact = attachment_set_artifact()
    attachment = artifact["payload"]["attachments"][0]
    attachment["selectionDecision"] = "ambiguous"
    attachment["selectedCandidateId"] = None
    attachment["selectedSourceRef"] = None
    attachment["freshness"] = "unknown"
    attachment["decisiveEvidence"] = []
    attachment["rejectionReasons"] = ["multiple-strongest-candidates"]
    artifact["artifactId"] = detached_content_id(artifact)

    connection = memory_database()
    project_envelopes(connection, [artifact])
    assert connection.execute(
        """
        SELECT selection_decision,selected_candidate_id,source_local_id,
               semantic_acceptance,rejection_reasons_json
        FROM proofir_v3_attachments
        """
    ).fetchone() == (
        "ambiguous",
        None,
        None,
        0,
        '["multiple-strongest-candidates"]',
    )


def test_attachment_constraints_reject_authority_and_policy_drift() -> None:
    connection = memory_database()
    project_envelopes(connection, [attachment_set_artifact()])
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE proofir_v3_attachments SET semantic_acceptance=1"
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE proofir_v3_attachment_candidates SET method='invented'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE proofir_v3_attachment_candidates SET policy_version='foreign'"
        )
    connection.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("DELETE FROM proofir_v3_attachment_candidates")
        connection.commit()
    connection.rollback()


def test_sqlite_persists_the_native_resolver_decision_without_reranking() -> None:
    source_ref = ref("surface", "surface:1")
    surface = {
        "declarationName": "Alias",
        "environmentRef": ENVIRONMENT,
        "declarationFingerprint": "sha256:" + "f" * 64,
        "declarationRef": "lean-decl:Fixture.goal",
        "sourcePath": "Fixture/Main.lean",
        "contentHash": "sha256:" + "c" * 64,
        "sourceRange": {"startLine": 1, "endLine": 2},
        "module": "Fixture.Main",
    }
    declaration = {
        "id": "declaration:Fixture.goal",
        "declaration": "Fixture.goal",
        "declarationRef": "lean-decl:Fixture.goal",
        "environmentRef": ENVIRONMENT,
        "declarationFingerprint": "sha256:" + "f" * 64,
        "sourceRef": source_ref,
        "sourcePath": "Fixture/Main.lean",
        "contentHash": "sha256:" + "c" * 64,
        "sourceRange": {"startLine": 1, "endLine": 2},
        "module": "Fixture.Main",
    }
    decision = resolve_attachment(surface, [declaration])
    artifact = attachment_set_artifact()
    artifact["payload"]["resolver"] = decision["resolver"]
    artifact["payload"]["attachments"] = [
        {
            "subjectRef": ref("statement", "statement:goal"),
            **{
                key: decision[key]
                for key in (
                    "selectionDecision",
                    "selectedCandidateId",
                    "selectedSourceRef",
                    "candidates",
                    "freshness",
                    "decisiveEvidence",
                    "rejectionReasons",
                    "semanticAcceptance",
                )
            },
        }
    ]
    artifact["artifactId"] = detached_content_id(artifact)

    connection = memory_database()
    project_envelopes(connection, [artifact])
    projected = connection.execute(
        """
        SELECT selection_decision,selected_candidate_id,freshness,
               decisive_evidence_json,rejection_reasons_json,semantic_acceptance
        FROM proofir_v3_attachments
        """
    ).fetchone()
    assert projected == (
        decision["selectionDecision"],
        decision["selectedCandidateId"],
        decision["freshness"],
        json.dumps(decision["decisiveEvidence"], sort_keys=True, separators=(",", ":")),
        json.dumps(decision["rejectionReasons"], sort_keys=True, separators=(",", ":")),
        0,
    )
    candidate = connection.execute(
        """
        SELECT declaration_id,method,confidence,freshness,rank,policy_version,
               decisive_evidence_json,rejection_reasons_json
        FROM proofir_v3_attachment_candidates
        """
    ).fetchone()
    expected = decision["candidates"][0]
    assert candidate == (
        expected["declarationId"],
        expected["method"],
        expected["confidence"],
        expected["freshness"],
        expected["rank"],
        expected["policyVersion"],
        json.dumps(expected["decisiveEvidence"], sort_keys=True, separators=(",", ":")),
        json.dumps(expected["rejectionReasons"], sort_keys=True, separators=(",", ":")),
    )


def test_identical_artifacts_are_idempotent_but_conflicts_roll_back() -> None:
    artifact = claim_artifact()
    connection = memory_database()
    project_envelopes(connection, [artifact, copy.deepcopy(artifact)])
    assert projection_counts(connection)["artifacts"] == 1

    conflict = copy.deepcopy(artifact)
    conflict["payload"]["claimId"] = "claim:conflict"
    # Deliberately retain the old content ID: validation must reject before deletion.
    before = projection_counts(connection)
    with pytest.raises(ProofIRV3Error):
        project_envelopes(connection, [conflict])
    assert projection_counts(connection) == before


def test_oversized_batch_is_rejected_before_any_projection_row() -> None:
    connection = memory_database()
    oversized = [claim_artifact()] * (MAX_COLLECTION_ITEMS + 1)
    with pytest.raises(ProofIRV3Error, match="batch exceeds item limit"):
        project_envelopes(connection, oversized)
    assert projection_counts(connection)["artifacts"] == 0


def test_query_plans_use_named_access_paths() -> None:
    connection = memory_database()
    project_envelopes(connection, list(native_artifacts().values()))
    cases = [
        (
            "SELECT * FROM proofir_v3_claims WHERE statement_owner_artifact_id=? AND statement_kind=? AND statement_local_id=? ORDER BY content_artifact_id,claim_id",
            (
                native_artifacts()["proofir.claim"]["artifactId"],
                "statement",
                "statement:goal",
            ),
            "idx_v3_claim_subject",
        ),
        (
            "SELECT * FROM proofir_v3_step_premises WHERE content_artifact_id=? AND step_local_id=? ORDER BY ordinal",
            (native_artifacts()["proofir.derivation"]["artifactId"], "step:1"),
            "sqlite_autoindex_proofir_v3_step_premises_1",
        ),
        (
            "SELECT * FROM proofir_v3_observations WHERE owner_content_artifact_id=? AND subject_kind=? AND subject_local_id=?",
            (
                native_artifacts()["proofir.governance-observation"]["artifactId"],
                "statement",
                "statement:goal",
            ),
            "idx_v3_observation_subject",
        ),
        (
            "SELECT * FROM proofir_v3_attachments WHERE subject_owner_artifact_id=? AND subject_kind=? AND subject_local_id=?",
            (
                native_artifacts()["proofir.attachment-set"]["artifactId"],
                "statement",
                "statement:goal",
            ),
            "idx_v3_attachment_subject",
        ),
        (
            "SELECT * FROM proofir_v3_attachment_candidates WHERE source_owner_artifact_id=? AND source_kind=? AND source_local_id=?",
            (
                native_artifacts()["proofir.attachment-set"]["artifactId"],
                "surface",
                "surface:1",
            ),
            "idx_v3_candidate_source",
        ),
        (
            "SELECT * FROM proofir_v3_extensions WHERE namespace=? ORDER BY content_artifact_id",
            ("example.fixture/v1",),
            "idx_v3_extension_namespace",
        ),
    ]
    for sql, parameters, expected_index in cases:
        plan = connection.execute("EXPLAIN QUERY PLAN " + sql, parameters).fetchall()
        assert any(expected_index in str(row) for row in plan), (sql, plan)


def test_file_publication_is_fresh_atomic_and_integrity_checked(tmp_path: Path) -> None:
    destination = tmp_path / "proofir.sqlite3"
    first = native_artifacts()["proofir.claim"]
    publish_v3_database(destination, [first])
    original_bytes = destination.read_bytes()

    invalid = copy.deepcopy(first)
    invalid["payload"]["assertionState"] = "verified"
    invalid["artifactId"] = detached_content_id(invalid)
    with pytest.raises(ProofIRV3Error):
        publish_v3_database(destination, [invalid])
    assert destination.read_bytes() == original_bytes

    second = native_artifacts()["proofir.governance-observation"]
    metrics = publish_v3_database(destination, [second])
    assert metrics["integrity"] == "ok"
    assert metrics["foreignKeyViolations"] == 0
    assert metrics["databaseBytes"] == destination.stat().st_size
    with sqlite3.connect(destination) as connection:
        validate_v3_database(connection)
        payloads = [
            json.loads(row[0])
            for row in connection.execute(
                "SELECT canonical_json FROM proofir_v3_artifacts"
            )
        ]
    assert [payload["artifactId"] for payload in payloads] == [second["artifactId"]]


def test_projection_source_contains_no_silent_conflict_clause() -> None:
    source = Path("src/ladon/proofir_sqlite_v3.py").read_text(encoding="utf-8").upper()
    assert "INSERT OR REPLACE" not in source
    assert "INSERT OR IGNORE" not in source
