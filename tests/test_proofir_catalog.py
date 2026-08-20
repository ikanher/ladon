from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from support.proofir_v3_native import claim_artifact

from ladon.proof_search_index import (
    ProofSearchIndexError,
    build_proof_search_index,
    inspect_proof_search_index,
)
from ladon.proofir_catalog import (
    PROOFIR_CONFIG_RELATIVE_PATH,
    discover_catalog_artifacts,
)


def configure(
    repo: Path,
    artifacts: list[str],
    *,
    relationships: list[dict[str, str]] | None = None,
    **limits: int,
) -> None:
    manifest = {"artifacts": artifacts}
    if limits:
        manifest["limits"] = limits
    if relationships:
        manifest["relationships"] = relationships
    path = repo / PROOFIR_CONFIG_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")


def test_catalog_records_supported_and_unknown_kinds_without_raw_payload(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    supported = repo / "surface.json"
    supported.write_text(
        json.dumps({"artifactKind": "proof_ir_lean_surface_bundle", "schemaVersion": 1, "surfaces": []}),
        encoding="utf-8",
    )
    unknown = repo / "unknown.json"
    unknown.write_text(json.dumps({"artifactKind": "future_kind", "payload": "x"}), encoding="utf-8")
    configure(repo, ["surface.json", "unknown.json"])

    result = build_proof_search_index(repo)

    assert result.payload["counts"]["proofirArtifacts"] == 2
    with sqlite3.connect(result.index_path) as connection:
        rows = connection.execute(
            "SELECT artifact_kind, metadata_json FROM proofir_artifacts ORDER BY path"
        ).fetchall()
    assert rows[1][0] == "future_kind"
    assert "payload" not in rows[1][1]
    status = inspect_proof_search_index(repo)
    assert status["counts"]["proofir_artifacts"] == 2


def test_catalog_marks_malformed_input_and_no_config_is_not_empty(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    malformed = repo / "broken.json"
    malformed.write_text("{broken", encoding="utf-8")
    configure(repo, ["broken.json"])

    result = build_proof_search_index(repo)
    assert result.payload["counts"]["proofirDiagnostics"] == 1
    with sqlite3.connect(result.index_path) as connection:
        assert connection.execute(
            "SELECT state FROM proofir_artifacts"
        ).fetchone()[0] == "malformed"

    no_config = tmp_path / "no-config"
    no_config.mkdir()
    (no_config / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    no_config_result = build_proof_search_index(no_config)
    assert no_config_result.payload["counts"]["proofirArtifacts"] == 0
    with no_config_result.index_path.open("rb") as stream:
        assert b"not-configured" in stream.read()


def test_valid_v3_catalog_artifact_is_projected_into_shared_index(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    artifact = repo / "artifact.json"
    artifact.write_text(json.dumps(claim_artifact()), encoding="utf-8")
    configure(repo, ["artifact.json"])
    result = build_proof_search_index(repo)
    assert result.payload["counts"]["proofirV3Artifacts"] == 1
    with sqlite3.connect(result.index_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM proofir_v3_artifacts").fetchone()[0] == 1


def test_catalog_rejects_escape_and_limits_before_publish(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    configure(repo, ["../outside.json"])
    with pytest.raises(ProofSearchIndexError, match="escapes repository"):
        build_proof_search_index(repo)

    configure(repo, ["large.json"], maxArtifactBytes=4)
    (repo / "large.json").write_text("{}{}{}", encoding="utf-8")
    # The manifest itself remains valid; this verifies the explicit limit path.
    with pytest.raises(ProofSearchIndexError, match="byte limit"):
        build_proof_search_index(repo)


def test_catalog_discovery_is_sorted_and_hashes_bytes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "b.json").write_text("{}", encoding="utf-8")
    (repo / "a.json").write_text("{}", encoding="utf-8")
    configure(repo, ["*.json"])

    config, artifacts = discover_catalog_artifacts(repo)

    assert config.configured is True
    assert [artifact.relative_path for artifact in artifacts] == ["a.json", "b.json"]
    assert all(len(artifact.sha256) == 64 for artifact in artifacts)


def test_catalog_keeps_file_digest_separate_from_validated_artifact_id(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    artifact_path = repo / "claim.json"
    artifact = claim_artifact()
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    configure(repo, ["claim.json"])

    _, artifacts = discover_catalog_artifacts(repo)

    observed = artifacts[0]
    assert str(observed.file_digest) == "sha256:" + observed.sha256
    assert observed.content_artifact_id == artifact["artifactId"]
    assert observed.file_digest != observed.content_artifact_id


def test_catalog_persists_configured_relationships_and_rebuilds_atomically(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    for name in ("surface.json", "replay.json"):
        (repo / name).write_text(
            json.dumps(claim_artifact()),
            encoding="utf-8",
        )
    configure(
        repo,
        ["surface.json", "replay.json"],
        relationships=[
            {"source": "replay.json", "target": "surface.json", "kind": "replays"}
        ],
        maxArtifactBytes=1024,
    )
    first = build_proof_search_index(repo)
    first_bytes = first.index_path.read_bytes()
    second = build_proof_search_index(repo)

    assert first.payload["counts"]["proofirRelations"] == 1
    assert second.index_path.read_bytes() == first_bytes
    with sqlite3.connect(second.index_path) as connection:
        path_plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT artifact_id FROM proofir_artifacts WHERE path = ? AND sha256 = ?",
            ("surface.json", "x" * 64),
        ).fetchall()
        details = json.loads(
            connection.execute("SELECT details_json FROM proofir_relations").fetchone()[
                0
            ]
        )
    assert any("idx_proofir_artifact_path_hash" in str(row) for row in path_plan)
    observation = details["linkObservation"]
    assert observation["observationKind"] == "manifest-assertion"
    assert observation["linkResult"] == "unbound"
    assert observation["semanticAcceptance"] is False
    assert observation["diagnostics"] == [
        "missing-source-endpoint",
        "missing-target-endpoint",
    ]

    configure(repo, ["surface.json"], maxArtifactBytes=1)
    with pytest.raises(ProofSearchIndexError, match="byte limit"):
        build_proof_search_index(repo)
    assert second.index_path.read_bytes() == first_bytes
