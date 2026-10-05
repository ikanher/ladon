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
    status = main(["proof-search", "search", "type-text", "--repo-root", str(tmp_path), "--pattern", "Nat", "--limit", "1", "--diagnostic-limit", "1", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["schema"] == "ladon-proof-search-type-text-result-v2"
    assert payload["results"][0]["authority"] == "lexical_shortlist"
    assert "Nat" in payload["results"][0]["typeText"]
    assert payload["freshness"] == "stored"
    assert payload["matched"] >= payload["returned"] == 1
    assert payload["matchedExact"] is True
    assert payload["diagnostics"]


def test_retired_type_alias_fails_before_index_access(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "proof-search", "search", "type", "--repo-root", str(tmp_path),
            "--pattern", "Nat", "--format", "json",
        ]
    )
    captured = capsys.readouterr()
    assert status != 0
    assert captured.out == ""
    diagnostic = json.loads(captured.err)
    assert diagnostic["exitClass"] == "invocation"
    assert diagnostic["migration"] == "use 'search type-text'"


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


def test_type_text_reports_field_contributions_and_bounded_omissions(
    tmp_path: Path, capsys
) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem first : Nat := 1\ntheorem second : Nat := 2\n",
        encoding="utf-8",
    )
    build_proof_search_index(tmp_path)
    status = main(
        [
            "proof-search",
            "search",
            "type-text",
            "--repo-root",
            str(tmp_path),
            "--pattern",
            "Nat",
            "--limit",
            "1",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    row = payload["results"][0]
    assert row["fieldContributions"]["typeText"]
    assert row["typeTextBytes"] >= 0
    assert payload["coverage"]["fieldContributionCounts"]["typeText"] == 1
    assert payload["coverage"]["shortlistMatchedLowerBound"] >= 2
    assert payload["coverage"]["populationComplete"] is False
    assert payload["omissions"][0]["kind"] == "result-cap"


def test_type_text_matching_is_literal_and_case_consistent(tmp_path: Path, capsys) -> None:
    (tmp_path / "Main.lean").write_text("theorem first : Nat := 1\n", encoding="utf-8")
    build_proof_search_index(tmp_path)
    for pattern, expected in (("nat", 1), ("%", 0), ("_", 0)):
        status = main(
            [
                "proof-search", "search", "type-text", "--repo-root", str(tmp_path),
                "--pattern", pattern, "--format", "json",
            ]
        )
        payload = json.loads(capsys.readouterr().out)
        assert status == 0
        assert len(payload["results"]) == expected
        if expected:
            assert payload["results"][0]["fieldContributions"]["typeText"] is True
