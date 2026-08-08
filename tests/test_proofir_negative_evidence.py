from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ladon.proof_search_index import build_proof_search_index
from ladon.proofir_coverage import query_proofir_coverage
from ladon.proofir_triage import query_proofir_triage


def test_unconfigured_coverage_is_not_observed_absence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def root : Nat := 1\n", encoding="utf-8")
    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        coverage = query_proofir_coverage(db, theorem="missing")
    assert coverage["families"]["surface"]["state"] == "not-configured"
    assert "not proof" in coverage["nonclaims"][0]


def test_configured_empty_and_unattached_surface_are_distinct(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def root : Nat := 1\n", encoding="utf-8")
    bundle = {"artifactKind": "proof_ir_lean_surface_bundle", "schemaVersion": 1, "surfaces": [{"surfaceId": "surface.unattached", "declarationName": "not_in_lean", "sourcePath": "Main.lean"}]}
    (repo / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    (repo / ".ladon").mkdir()
    (repo / ".ladon" / "proofir.json").write_text(json.dumps({"artifacts": ["bundle.json"]}), encoding="utf-8")
    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        db.row_factory = sqlite3.Row
        coverage = query_proofir_coverage(db)
        triage = query_proofir_triage(db)
    assert coverage["families"]["surface"]["state"] == "observed"
    assert any(row["ruleId"] == "unattached_surface" for row in triage["findings"])
    assert any(row["ruleId"] == "disconnected_evidence" for row in triage["findings"])

