from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ladon.proof_search_index import build_proof_search_index
from ladon.proofir_triage import query_proofir_triage


def test_triage_is_deterministic_and_bounded(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Main.lean").write_text("def root : Nat := 1\n", encoding="utf-8")
    artifact = {"artifactKind": "future_kind", "payload": "unsupported"}
    (repo / "unknown.json").write_text(json.dumps(artifact), encoding="utf-8")
    (repo / ".ladon").mkdir()
    (repo / ".ladon" / "proofir.json").write_text(json.dumps({"artifacts": ["unknown.json"]}), encoding="utf-8")
    result = build_proof_search_index(repo)
    with sqlite3.connect(result.index_path) as db:
        first = query_proofir_triage(db, limit=1)
        second = query_proofir_triage(db, limit=1)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["families"]["unsupported_artifact"]["returned"] == 1
    assert len(first["findings"]) <= 1

