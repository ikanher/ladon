from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ladon.proof_search_index import build_proof_search_index


def _configure(repo: Path, names: list[str]) -> None:
    path = repo / ".ladon" / "proofir.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"artifacts": names}), encoding="utf-8")


def test_surface_bundle_and_claim_rows_preserve_admitted_fields(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("theorem root : True := True.intro\n", encoding="utf-8")
    bundle = {
        "schemaVersion": 1,
        "artifactKind": "proof_ir_lean_surface_bundle",
        "source": {"sourcePath": "Main.lean", "contentHash": "sha256:source"},
        "surfaces": [{
            "surfaceId": "surface.root", "claimId": "claim.root",
            "declarationName": "root", "sourcePath": "Main.lean",
            "sourceRange": {"startLine": 1, "endLine": 1},
            "contentHash": "sha256:source", "authority": "lean_kernel_external",
            "proofTrust": "lean_source_marker_extracted",
            "replayBoundary": {"status": "not_replayed_by_extractor"},
            "extractorGuarantee": "source_surface_only",
        }],
    }
    (repo / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    _configure(repo, ["bundle.json"])

    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        surface = db.execute(
            "SELECT surface_id, declaration_name, proof_trust FROM proofir_surfaces"
        ).fetchone()
        claim = db.execute("SELECT claim_id, proof_trust FROM proofir_claims").fetchone()
    assert surface == ("surface.root", "root", "lean_source_marker_extracted")
    assert claim == ("claim.root", "lean_source_marker_extracted")
    assert result.payload["counts"]["proofirSurfaces"] == 1
    assert result.payload["counts"]["proofirClaims"] == 1


def test_replay_relation_distinguishes_related_stale_and_foreign_surfaces(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("theorem root : True := True.intro\n", encoding="utf-8")
    bundle = {
        "artifactKind": "proof_ir_lean_surface_bundle", "schemaVersion": 1,
        "surfaces": [{"surfaceId": "surface.root", "declarationName": "root"}],
    }
    replay = {
        "artifactKind": "proof_ir_lean_replay_provenance", "schemaVersion": 1,
        "provenanceId": "replay.root", "module": "Main", "returncode": 0,
        "surfaceBundle": {"path": "bundle.json", "contentHash": "sha256:WRONG"},
        "surfaces": [{"surfaceId": "surface.root"}, {"surfaceId": "surface.foreign"}],
    }
    (repo / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    (repo / "replay.json").write_text(json.dumps(replay), encoding="utf-8")
    _configure(repo, ["bundle.json", "replay.json"])

    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        statuses = db.execute(
            "SELECT surface_id, status FROM proofir_replay_surfaces ORDER BY surface_id"
        ).fetchall()
    assert statuses == [("surface.foreign", "stale"), ("surface.root", "stale")]
    assert result.payload["counts"]["proofirReplayRuns"] == 1
    assert result.payload["counts"]["proofirReplaySurfaces"] == 2
