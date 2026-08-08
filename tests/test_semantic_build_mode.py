from __future__ import annotations

import json
from pathlib import Path

from ladon.proof_search_index import build_proof_search_index
from ladon.semantic_build_mode import SemanticBuildRequest, cache_reusable, module_cache_key


def test_build_request_validates_modes_and_cache_identity() -> None:
    request = SemanticBuildRequest("hybrid", 4.0, "require-complete")
    identity = {"source": "a", "imports": ["b"], "helper": "v1"}
    record = {"cacheKey": module_cache_key(identity), "status": "complete"}
    assert request.mode == "hybrid"
    assert cache_reusable(record, identity)
    assert not cache_reusable(record, {**identity, "source": "changed"})


def test_build_payload_exposes_mode_and_publication(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    payload = build_proof_search_index(tmp_path, build_mode="hybrid", lean_timeout=3.0).payload
    assert payload["build"] == {"mode": "hybrid", "leanTimeout": 3.0, "semanticCompleteness": "allow-partial", "publication": "atomic"}
