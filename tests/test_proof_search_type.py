from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from ladon.cli import main
from ladon.proof_search_index import build_proof_search_index


def test_type_search_returns_lexical_shortlist_and_diagnostics(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem first : Nat := 1\ntheorem second : Nat := 2\n", encoding="utf-8"
    )
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "type", "--repo-root", str(tmp_path), "--pattern", "Nat", "--limit", "1", "--diagnostic-limit", "1", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["schema"] == "ladon-proof-search-type-result-v1"
    assert payload["results"][0]["authority"] == "lexical_shortlist"
    assert payload["diagnostics"]


def test_warm_sqlite_shortlist_has_bounded_latency(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    database = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(database) as connection:
        from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist
        query_type_shortlist(connection, TypeSearchRequest("Nat"))
        started = time.perf_counter()
        for _ in range(10):
            query_type_shortlist(connection, TypeSearchRequest("Nat"))
    assert (time.perf_counter() - started) < 1.0


def test_type_text_verify_includes_index_generation_evidence(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--pattern", "Nat", "--freshness", "verify", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["freshnessEvidence"]["generationIdentity"]


def test_type_text_module_scope_reports_population_evidence(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--pattern", "Nat", "--scope", "module", "--root", "Main", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["coverage"]["scope"]["kind"] == "module"
    assert payload["coverage"]["scope"]["modules"] == 1
