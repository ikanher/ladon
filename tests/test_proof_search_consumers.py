from __future__ import annotations

import sqlite3
from pathlib import Path

from ladon.proof_search_consumers import ConsumerRequest, query_consumers
from ladon.proof_search_index import build_proof_search_index


def test_missing_target_is_explicitly_unavailable(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    database = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(database) as connection:
        result = query_consumers(connection, ConsumerRequest("missing"))
    assert result["status"] == "unavailable"
    assert result["omissions"][0]["reason"] == "target_missing"


def test_symbol_frontier_is_populated_without_claiming_dependencies(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    database = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(database) as connection:
        result = query_consumers(connection, ConsumerRequest("value"))
    assert result["status"] == "complete"
    assert result["coverage"]["authority"] == "sqlite_semantic_dependency_index"
