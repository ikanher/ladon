"""Owner-qualified ProofIR dossier queries never borrow same-name evidence."""
from __future__ import annotations

import copy
import json

from support.proofir_v3_native import native_artifacts

from ladon import proofir_v3_queries as queries
from ladon.proofir_sqlite_v3 import create_v3_schema, project_envelopes
from ladon.proofir_v3 import detached_content_id


def _connection_with_claims():
    import sqlite3

    first = native_artifacts()["proofir.claim"]
    second = copy.deepcopy(first)
    second["producer"]["name"] = "second-owner"
    second["artifactId"] = detached_content_id(second)
    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    project_envelopes(connection, [first, second])
    return connection, first, second


def _subject_query(connection, subject, *, limit=20):
    query = getattr(queries, "query_v3_subject_evidence", None)
    assert callable(query), (
        "the dossier owner lacks query_v3_subject_evidence(connection, "
        "{ownerArtifactId, kind, localId}, limit=...)"
    )
    return query(connection, subject, limit=limit)


def test_exact_subject_query_accepts_declarations_as_well_as_statements():
    import sqlite3

    derivation = native_artifacts()["proofir.derivation"]
    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    project_envelopes(connection, [derivation])

    declaration = {
        "ownerArtifactId": derivation["artifactId"],
        "kind": "declaration",
        "localId": "declaration:rule",
    }
    dossier = _subject_query(connection, declaration)

    assert dossier["status"] == "observed"
    assert dossier["subjects"]["rows"] == [
        {
            "ownerArtifactId": derivation["artifactId"],
            "environmentRef": derivation["environmentRef"],
            "kind": "declaration",
            "localId": "declaration:rule",
        }
    ]


def test_identical_local_ids_from_different_owners_never_borrow_evidence():
    connection, first, second = _connection_with_claims()
    first_subject = {
        "ownerArtifactId": first["artifactId"],
        "kind": "statement",
        "localId": "statement:goal",
    }
    second_subject = {**first_subject, "ownerArtifactId": second["artifactId"]}

    first_dossier = _subject_query(connection, first_subject)
    second_dossier = _subject_query(connection, second_subject)

    assert [row["ownerArtifactId"] for row in first_dossier["subjects"]["rows"]] == [
        first["artifactId"]
    ]
    assert [row["ownerArtifactId"] for row in second_dossier["subjects"]["rows"]] == [
        second["artifactId"]
    ]
    assert {row["artifactId"] for row in first_dossier["claims"]["rows"]} == {
        first["artifactId"]
    }
    assert {row["artifactId"] for row in second_dossier["claims"]["rows"]} == {
        second["artifactId"]
    }


def test_exact_subject_does_not_promote_theorem_name_coverage():
    connection, artifact, _other = _connection_with_claims()
    # The owner reports theorem-name coverage, but that selector cannot certify
    # that coverage applies to an independently selected exact subject.
    connection.execute(
        "UPDATE proofir_v3_coverage SET population_kind='theorem-evidence', "
        "selector_json=? WHERE content_artifact_id=?",
        (json.dumps({"theorem": "statement:goal"}, separators=(",", ":")), artifact["artifactId"]),
    )
    subject = {
        "ownerArtifactId": artifact["artifactId"],
        "kind": "statement",
        "localId": "statement:goal",
    }

    dossier = _subject_query(connection, subject)

    assert dossier["coverage"]["applicability"] == "unavailable"
    assert dossier["coverage"]["rows"] == []


def test_existing_theorem_query_keeps_name_based_multi_owner_behavior():
    connection, first, second = _connection_with_claims()

    dossier = queries.query_v3_theorem_evidence(
        connection, "statement:goal", limit=20
    )

    assert dossier["status"] == "observed"
    assert {
        row["ownerArtifactId"] for row in dossier["subjects"]["rows"]
    } == {first["artifactId"], second["artifactId"]}
    assert {row["artifactId"] for row in dossier["claims"]["rows"]} == {
        first["artifactId"], second["artifactId"]
    }

