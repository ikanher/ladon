from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from ladon.proof_search_index import build_proof_search_index
from ladon.proofir_queries import EvidenceQueryBounds, query_theorem_dossier


def _repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    source = "theorem exact_root : True := True.intro\n"
    (repo / "Main.lean").write_text(source, encoding="utf-8")
    digest = hashlib.sha256(source.encode()).hexdigest()
    bundle = {"artifactKind": "proof_ir_lean_surface_bundle", "schemaVersion": 1, "surfaces": [{"surfaceId": "surface.exact", "claimId": "claim.exact", "declarationName": "exact_root", "sourcePath": "Main.lean", "contentHash": f"sha256:{digest}", "status": "conditional", "authority": "external", "proofTrust": "quoted", "replayBoundary": {"status": "not_replayed_by_extractor"}, "extractorGuarantee": "source_surface_only"}]}
    replay = {"artifactKind": "proof_ir_lean_replay_provenance", "schemaVersion": 1, "provenanceId": "replay.exact", "module": "Main", "returncode": 0, "guarantee": "repository_local_build", "surfaceBundle": {"path": "bundle.json", "contentHash": "sha256:PLACEHOLDER"}, "surfaces": [{"surfaceId": "surface.exact"}]}
    (repo / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    replay["surfaceBundle"]["contentHash"] = f"sha256:{hashlib.sha256((repo / 'bundle.json').read_bytes()).hexdigest()}"
    (repo / "replay.json").write_text(json.dumps(replay), encoding="utf-8")
    (repo / ".ladon").mkdir()
    (repo / ".ladon" / "proofir.json").write_text(json.dumps({"artifacts": ["bundle.json", "replay.json"]}), encoding="utf-8")
    return repo, digest


def test_theorem_dossier_has_separate_evidence_sections_and_exact_replay(tmp_path: Path) -> None:
    repo, _ = _repo(tmp_path)
    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        db.row_factory = sqlite3.Row
        dossier = query_theorem_dossier(db, "exact_root")
    assert dossier["schema"] == "ladon-proofir-theorem-dossier-v1"
    assert {"declaration", "attachments", "surfaces", "claims", "replay", "obligationContext", "lineage", "diagnostics", "coverage", "nonclaims"} <= dossier.keys()
    assert dossier["surfaces"]["rows"][0]["attachment"]["confidence"] == "highest"
    assert dossier["surfaces"]["rows"][0]["status"] == "conditional"
    assert dossier["claims"]["rows"][0]["status"] == "not_replayed_by_extractor"
    assert dossier["replay"]["rows"][0]["returnCode"] == 0
    assert dossier["claims"]["rows"][0]["status"] != "replayed"


def test_unattached_and_duplicate_names_do_not_get_inferred(tmp_path: Path) -> None:
    repo, _ = _repo(tmp_path)
    (repo / "extra.json").write_text(json.dumps({"artifactKind": "proof_ir_lean_surface_bundle", "schemaVersion": 1, "surfaces": [{"surfaceId": "surface.near", "declarationName": "nearby", "sourcePath": "Main.lean"}]}), encoding="utf-8")
    (repo / ".ladon" / "proofir.json").write_text(json.dumps({"artifacts": ["bundle.json", "replay.json", "extra.json"]}), encoding="utf-8")
    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        db.row_factory = sqlite3.Row
        dossier = query_theorem_dossier(db, "missing_theorem", bounds=EvidenceQueryBounds(surfaces=1))
    assert dossier["declaration"]["candidates"] == []
    assert dossier["surfaces"]["rows"] == []
    assert "context-only" not in dossier["attachments"]


def test_claim_materialization_is_set_oriented(tmp_path: Path) -> None:
    repo, _ = _repo(tmp_path)
    result = build_proof_search_index(repo)
    statements: list[str] = []
    with sqlite3.connect(result.index_path) as db:
        db.row_factory = sqlite3.Row
        db.set_trace_callback(statements.append)
        query_theorem_dossier(db, "exact_root")
    claim_selects = [sql for sql in statements if "SELECT c.claim_row_id" in sql]
    assert len(claim_selects) == 1
