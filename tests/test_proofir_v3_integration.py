from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
from support.proofir_v3_native import attachment_set_artifact, claim_artifact

from ladon.proof_search_schema import create_proof_search_schema
from ladon.proof_search_v3_projection import project_v3_catalog
from ladon.proofir_catalog import CatalogArtifact
from ladon.proofir_sqlite_v3 import project_envelopes
from ladon.proofir_v3 import detached_content_id
from ladon.proofir_v3_queries import query_v3_theorem_evidence


def _cataloged(path: Path, artifact: dict[str, object]) -> CatalogArtifact:
    raw = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
    path.write_bytes(raw)
    return CatalogArtifact(
        relative_path=path.name,
        path=path,
        byte_size=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
        artifact_kind=str(artifact["artifactKind"]),
        schema_version="3.0",
        state="cataloged",
        metadata_json="{}",
    )


def _with_theorem_selector(theorem: str) -> dict[str, object]:
    artifact = copy.deepcopy(claim_artifact())
    artifact["coverage"]["population"]["selector"] = {"theorem": theorem}
    artifact["artifactId"] = detached_content_id(artifact)
    return artifact


def test_catalog_projection_is_one_atomic_batch_and_detects_snapshot_drift(
    tmp_path: Path,
) -> None:
    first = _cataloged(tmp_path / "first.json", claim_artifact())
    second_value = _with_theorem_selector("statement:goal")
    second = _cataloged(tmp_path / "second.json", second_value)
    snapshot = SimpleNamespace(proofir_artifacts=(first, second))

    connection = sqlite3.connect(":memory:")
    create_proof_search_schema(connection)
    assert project_v3_catalog(connection, snapshot) == 2
    before = connection.execute(
        "SELECT content_artifact_id FROM proofir_v3_artifacts "
        "ORDER BY content_artifact_id"
    ).fetchall()

    second.path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="changed after catalog capture"):
        project_v3_catalog(connection, snapshot)

    assert (
        connection.execute(
            "SELECT content_artifact_id FROM proofir_v3_artifacts "
            "ORDER BY content_artifact_id"
        ).fetchall()
        == before
    )


def test_theorem_evidence_uses_native_subject_columns_and_separate_sections() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    project_envelopes(connection, [claim_artifact()])

    result = query_v3_theorem_evidence(connection, "statement:goal", limit=10)

    assert result["status"] == "observed"
    assert result["subjects"]["rows"] == [
        {
            "ownerArtifactId": claim_artifact()["artifactId"],
            "environmentRef": claim_artifact()["environmentRef"],
            "kind": "statement",
            "localId": "statement:goal",
        }
    ]
    assert result["claims"]["rows"][0]["assertionState"] == "asserted"
    assert set(result) >= {
        "subjects",
        "claims",
        "observations",
        "derivations",
        "attachments",
        "coverage",
        "omissions",
        "navigation",
        "limitations",
    }
    assert result["nonclaims"] == [
        "ProofIR records environment-scoped evidence, not unqualified theorem truth.",
        "Navigation rows are not complete derivation slices.",
    ]


def test_theorem_evidence_filters_coverage_by_exact_theorem_selector() -> None:
    matching = _with_theorem_selector("statement:goal")
    unrelated = _with_theorem_selector("statement:other")
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    project_envelopes(connection, [matching, unrelated])

    result = query_v3_theorem_evidence(connection, "statement:goal", limit=10)

    assert [row["artifactId"] for row in result["coverage"]["rows"]] == [
        matching["artifactId"]
    ]
    assert result["coverage"]["rows"][0]["selector"] == {"theorem": "statement:goal"}
    assert result["observations"]["rows"] == []


def test_theorem_dossier_quotes_attachment_decision_without_truth_promotion() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    project_envelopes(connection, [attachment_set_artifact()])

    result = query_v3_theorem_evidence(connection, "statement:goal", limit=10)

    attachment = result["attachments"]["rows"][0]
    assert attachment["selectionDecision"] == "selected"
    assert attachment["selectedCandidateId"] == "declaration:Fixture.goal"
    assert attachment["decisiveEvidence"]
    assert attachment["semanticAcceptance"] is False
    assert "trusted" not in attachment and "verified" not in attachment


def test_theorem_evidence_does_not_relabel_unscoped_coverage_as_absence() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    project_envelopes(connection, [claim_artifact()])

    result = query_v3_theorem_evidence(connection, "statement:goal", limit=10)

    assert result["coverage"]["rows"] == []
    assert result["coverage"]["applicability"] == "unavailable"
    assert result["coverage"]["reason"] == "no exact theorem selector"
